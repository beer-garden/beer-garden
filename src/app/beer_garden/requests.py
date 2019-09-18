import json
import logging
from collections.abc import Sequence

import re
import six
import urllib3
from builtins import str
from functools import reduce
from mongoengine import Q
from requests import Session
from threading import Event

import beer_garden
from beer_garden.events import publish_event
from beer_garden.metrics import request_created, request_started, request_completed
from beer_garden.bg_utils.mongo.models import Choices, Request, System
from brewtils.choices import parse
from brewtils.errors import ModelValidationError, RequestPublishException, ConflictError
from brewtils.models import Events
from brewtils.schema_parser import SchemaParser

logger = logging.getLogger(__name__)

request_map = {}


class RequestValidator(object):
    def __init__(self, validator_config):
        self.logger = logging.getLogger(__name__)

        self._command_timeout = validator_config.command.timeout

        self._session = Session()
        if not validator_config.url.ca_verify:
            urllib3.disable_warnings()
            self._session.verify = False
        elif validator_config.url.ca_cert:
            self._session.verify = validator_config.url.ca_cert

    def validate_request(self, request):
        """Validation to be called before you save a request from a user

        :param request: The request to validate
        """
        self.logger.debug("Validating request")

        system = self.get_and_validate_system(request)
        command = self.get_and_validate_command_for_system(request, system)
        request.parameters = self.get_and_validate_parameters(request, command)
        request.has_parent = self.get_and_validate_parent(request)

        return request

    def get_and_validate_parent(self, request):
        """Ensure that a Request's parent request hasn't already completed.

        :param request: The request to validate
        :return: Boolean indicating if this request has a parent
        :raises ConflictError: The parent request has already completed
        """
        if not request.parent:
            return False

        if request.parent.status in Request.COMPLETED_STATUSES:
            raise ConflictError("Parent request has already completed")

        return True

    def get_and_validate_system(self, request):
        """Ensure there is a system in the DB that corresponds to this Request.

        :param request: The request to validate
        :return: The system corresponding to this Request
        :raises ModelValidationError: There is no system that corresponds to this Request
        """
        system = System.find_unique(request.system, request.system_version)
        if system is None:
            raise ModelValidationError(
                "Could not find System named '%s' matching version '%s'"
                % (request.system, request.system_version)
            )

        if request.instance_name not in system.instance_names:
            raise ModelValidationError(
                "Could not find instance with name '%s' in system '%s'"
                % (request.instance_name, system.name)
            )

        self.logger.debug(
            "Found System %s-%s" % (request.system, request.instance_name)
        )
        return system

    def get_and_validate_command_for_system(self, request, system=None):
        """Ensure the System has a command with a name that matches this request.

        :param request: The request to validate
        :param system: Specifies a System to use. If None a system lookup will be attempted.
        :return: The database command
        :raises ValidationError: if the request or command is invalid
        """
        self.logger.debug("Getting and Validating Command for System")
        if system is None:
            self.logger.debug("No System was passed in")
            system = self.get_and_validate_system(request)

        if request.command is None:
            raise ModelValidationError(
                "Could not validate command because it was None."
            )

        self.logger.debug(
            "Looking through Command Names to find the Command Specified."
        )
        command_names = []
        for command in system.commands:
            if command.name == request.command:
                self.logger.debug("Found Command with name: %s" % request.command)

                if request.command_type is None:
                    request.command_type = command.command_type
                elif command.command_type != request.command_type:
                    raise ModelValidationError(
                        "Command Type for Request was %s but the command specified "
                        "the type as %s" % (request.command_type, command.command_type)
                    )

                if request.output_type is None:
                    request.output_type = command.output_type
                elif command.output_type != request.output_type:
                    raise ModelValidationError(
                        "Output Type for Request was %s but the command specified "
                        "the type as %s" % (request.output_type, command.output_type)
                    )

                return command

            command_names.append(command.name)

        raise ModelValidationError(
            "No Command with name: %s could be found. Valid Commands for %s are: %s"
            % (request.command, system.name, command_names)
        )

    def get_and_validate_parameters(
        self, request, command=None, command_parameters=None, request_parameters=None
    ):
        """Validates all request parameters

        Note: It is significant that we build the parameters as a separate object and then assign
        it. This is significant because when you are setting a value to None, mongoengine
        interprets this as "mark the item for deletion" meaning that when you save that attribute,
        it will actually get deleted. Sounds weird right? Well at least you didn't have to
        troubleshoot it.

        :param request: The Request to validate
        :param command: The the Command for this request. Will attempt to discover if None.
        :param command_parameters:  The command parameters.
        :param request_parameters: The request parameters.
        :return: The updated Parameters, ready to be saved to the database
        """
        self.logger.debug("Updating and Validating Parameters")

        if command is None:
            self.logger.debug("No Command Provided.")
            command = self.get_and_validate_command_for_system(request)

        if command_parameters is None:
            command_parameters = command.parameters

        if request_parameters is None:
            request_parameters = request.parameters

        self._validate_no_extra_request_parameter_keys(
            request_parameters, command_parameters
        )

        parameters_to_save = {}
        for command_parameter in command_parameters:
            self._validate_required_parameter_is_included_in_request(
                request, command_parameter, request_parameters
            )
            extracted_value = self._extract_parameter_value_from_request(
                request, command_parameter, request_parameters, command
            )
            self._validate_value_in_choices(request, extracted_value, command_parameter)
            self._validate_maximum(extracted_value, command_parameter)
            self._validate_minimum(extracted_value, command_parameter)
            self._validate_regex(extracted_value, command_parameter)
            parameters_to_save[command_parameter.key] = extracted_value

        self.logger.debug("Successfully Updated and Validated Parameters.")
        self.logger.debug("Parameters: %s", parameters_to_save)
        return parameters_to_save

    def _validate_value_in_choices(self, request, value, command_parameter):
        """Validate that the value(s) are valid according to the choice constraints"""
        if (
            value is not None
            and not command_parameter.optional
            and command_parameter.choices
            and command_parameter.choices.strict
        ):

            choices = command_parameter.choices

            def map_param_values(kv_pair_list):
                param_map = {}
                for param_name, param_ref in kv_pair_list:
                    if param_ref == "instance_name":
                        param_map[param_name] = request.instance_name
                    else:
                        param_map[param_name] = request.parameters[param_ref]

                return param_map

            if choices.type == "static":
                if isinstance(choices.value, list):
                    allowed_values = choices.value
                elif isinstance(choices.value, dict):
                    key = choices.details.get("key_reference")
                    if key is None:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Choices"
                            " with a dictionary value must specify a key_reference"
                            % command_parameter.key
                        )

                    if key == "instance_name":
                        key_reference_value = request.instance_name
                    else:
                        # Mongoengine stores None keys as 'null', so use that instead of None
                        key_reference_value = request.parameters.get(key) or "null"

                    allowed_values = choices.value.get(key_reference_value)
                    if allowed_values is None:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Choices"
                            " dictionary doesn't contain an entry with key '%s'"
                            % (command_parameter.key, key_reference_value)
                        )
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Choices value"
                        " must be a list or dictionary " % command_parameter.key
                    )
            elif choices.type == "url":
                parsed_value = parse(choices.value, parse_as="url")
                query_params = map_param_values(parsed_value["args"])

                response_json = json.loads(
                    self._session.get(parsed_value["address"], params=query_params).text
                )

                allowed_values = []
                for item in response_json:
                    if isinstance(item, dict):
                        allowed_values.append(item["value"])
                    else:
                        allowed_values.append(item)
            elif choices.type == "command":

                if isinstance(choices.value, six.string_types):
                    parsed_value = parse(choices.value, parse_as="func")

                    choices_request = Request(
                        system=request.system,
                        system_version=request.system_version,
                        instance_name=request.instance_name,
                        command=parsed_value["name"],
                        parameters=map_param_values(parsed_value["args"]),
                    )
                elif isinstance(choices.value, dict):
                    parsed_value = parse(choices.value["command"], parse_as="func")
                    choices_request = Request(
                        system=choices.value.get("system"),
                        system_version=choices.value.get("version"),
                        instance_name=choices.value.get("instance_name", "default"),
                        command=parsed_value["name"],
                        parameters=map_param_values(parsed_value["args"]),
                    )
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Choices value"
                        " must be a string or dictionary " % command_parameter.key
                    )

                response = process_request(
                    choices_request, wait_timeout=self._command_timeout
                )

                parsed_output = json.loads(response.output)
                if isinstance(parsed_output, list):
                    if len(parsed_output) < 1:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Result "
                            "of choices query was empty list" % command_parameter.key
                        )

                    if isinstance(parsed_output[0], dict):
                        allowed_values = [item["value"] for item in parsed_output]
                    else:
                        allowed_values = parsed_output
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Result of "
                        " choices query must be a list" % command_parameter.key
                    )
            else:
                raise ModelValidationError(
                    "Unable to validate choices for parameter '%s' - No valid type "
                    "specified (valid types are %s)"
                    % (command_parameter.key, Choices.TYPES)
                )

            if command_parameter.multi:
                for single_value in value:
                    if single_value not in allowed_values:
                        raise ModelValidationError(
                            "Value '%s' is not a valid choice for parameter with key '%s'. "
                            "Valid choices are: %s"
                            % (single_value, command_parameter.key, allowed_values)
                        )
            else:
                if value not in allowed_values:
                    raise ModelValidationError(
                        "Value '%s' is not a valid choice for parameter with key '%s'. "
                        "Valid choices are: %s"
                        % (value, command_parameter.key, allowed_values)
                    )

    def _validate_maximum(self, value, command_parameter):
        """Validate that the value(s) are below the specified maximum"""
        if value is not None and not command_parameter.optional:
            if command_parameter.maximum:
                if isinstance(value, Sequence):
                    if len(value) > command_parameter.maximum:
                        raise ModelValidationError(
                            "Length %s is greater than the maximum allowed length (%s) "
                            "for parameter %s"
                            % (
                                len(value),
                                command_parameter.maximum,
                                command_parameter.key,
                            )
                        )
                else:
                    if value > command_parameter.maximum:
                        raise ModelValidationError(
                            "Value %s is greater than the maximum allowed value (%s) "
                            "for parameter %s"
                            % (value, command_parameter.maximum, command_parameter.key)
                        )

    def _validate_minimum(self, value, command_parameter):
        """Validate that the value(s) are above the specified minimum"""
        if value is not None and not command_parameter.optional:
            if command_parameter.minimum:
                if isinstance(value, Sequence):
                    if len(value) < command_parameter.minimum:
                        raise ModelValidationError(
                            "Length %s is less than the minimum allowed length (%s) "
                            "for parameter %s"
                            % (
                                len(value),
                                command_parameter.minimum,
                                command_parameter.key,
                            )
                        )
                else:
                    if value < command_parameter.minimum:
                        raise ModelValidationError(
                            "Value %s is less than the minimum allowed value (%s) "
                            "for parameter %s"
                            % (value, command_parameter.minimum, command_parameter.key)
                        )

    def _validate_regex(self, value, command_parameter):
        """Validate that the value matches the regex"""
        if value is not None and not command_parameter.optional:
            if command_parameter.regex:
                if not re.match(command_parameter.regex, value):
                    raise ModelValidationError(
                        "Value %s does not match regular expression %s"
                        % (value, command_parameter.regex)
                    )

    def _extract_parameter_value_from_request(
        self, request, command_parameter, request_parameters, command
    ):
        """Extracts the expected value based on the parameter in the database,
        uses the default and validates the type of the request parameter"""
        request_value = request_parameters.get(
            command_parameter.key, command_parameter.default
        )

        if request_value is None and command_parameter.nullable:
            return None

        if command_parameter.multi:
            request_values = request_value
            if not isinstance(request_values, list):
                raise ModelValidationError(
                    "%s was specified as a list, "
                    "but was not provided as such" % command_parameter.key
                )

            value_to_return = []
            for value in request_values:
                value_to_return.append(
                    self._validate_parameter_based_on_type(
                        value, command_parameter, command, request
                    )
                )
        else:
            value_to_return = self._validate_parameter_based_on_type(
                request_value, command_parameter, command, request
            )

        return value_to_return

    def _validate_required_parameter_is_included_in_request(
        self, request, command_parameter, request_parameters
    ):
        """If the parameter is required but was not provided in the request_parameters and does
        not have a default, then raise a ValidationError"""
        self.logger.debug(
            "Validating that Required Parameters are included in the request."
        )
        if not command_parameter.optional:
            if (
                command_parameter.key not in request_parameters
                and command_parameter.default is None
            ):
                raise ModelValidationError(
                    "Required key '%s' not provided in request. Parameters are: %s"
                    % (command_parameter.key, request.parameters)
                )

    def _validate_no_extra_request_parameter_keys(
        self, request_parameters, command_parameters
    ):
        """Validate that all the parameters passed in were valid keys. If there is a key specified
        that is not noted in the database, then a validation error is thrown"""
        self.logger.debug("Validating Keys")
        valid_keys = [cp.key for cp in command_parameters]
        self.logger.debug("Valid Keys are : %s" % valid_keys)
        for key in request_parameters:
            if key not in valid_keys:
                raise ModelValidationError(
                    "Unknown key '%s' provided in the parameters. Valid Keys are: %s"
                    % (key, valid_keys)
                )

    def _validate_parameter_based_on_type(self, value, parameter, command, request):
        """Validates the value passed in, ensures the type matches.
        Recursive calls for dictionaries which also have nested parameters"""

        try:
            if value is None and not parameter.nullable:
                raise ModelValidationError(
                    "There is no value for parameter '%s' "
                    "and this field is not nullable." % parameter.key
                )
            elif parameter.type.upper() == "STRING":
                if isinstance(value, six.string_types):
                    return str(value)
                else:
                    raise TypeError("Invalid value for string (%s)" % value)
            elif parameter.type.upper() == "INTEGER":
                if int(value) != float(value):
                    raise TypeError("Invalid value for integer (%s)" % value)
                return int(value)
            elif parameter.type.upper() == "FLOAT":
                return float(value)
            elif parameter.type.upper() == "ANY":
                return value
            elif parameter.type.upper() == "BOOLEAN":
                if value in [True, False]:
                    return value
                else:
                    raise TypeError("Invalid value for boolean (%s)" % value)
            elif parameter.type.upper() == "DICTIONARY":
                dict_value = dict(value)
                if parameter.parameters:
                    self.logger.debug("Found Nested Parameters.")
                    return self.get_and_validate_parameters(
                        request, command, parameter.parameters, dict_value
                    )
                return dict_value
            elif parameter.type.upper() == "DATE":
                return int(value)
            elif parameter.type.upper() == "DATETIME":
                return int(value)
            else:
                raise ModelValidationError(
                    "Unknown type for parameter. Please contact a system administrator."
                )
        except TypeError as ex:
            self.logger.exception(ex)
            raise ModelValidationError(
                "Value for key: %s is not the correct type. Should be: %s"
                % (parameter.key, parameter.type)
            )
        except ValueError as ex:
            self.logger.exception(ex)
            raise ModelValidationError(
                "Value for key: %s is not the correct type. Should be: %s"
                % (parameter.key, parameter.type)
            )


def get_request(request_id):
    request = Request.objects.get(id=request_id)
    request.children = Request.objects(parent=request)

    return request


def get_requests(
    start=0, length=100, columns=None, order=None, search=None, include_children=False
):
    """Search for requests

    :return query_set: The QuerySet representing this query
    :return requested_fields: The fields to be returned for each Request
    """
    search_params = []
    requested_fields = []
    order_by = None
    overall_search = None
    hint = []

    query_set = Request.objects

    if columns:
        query_columns = []

        for column in columns:
            query_columns.append(column)

            if column["data"]:
                requested_fields.append(column["data"])

            if (
                "searchable" in column
                and column["searchable"]
                and column["search"]["value"]
            ):
                if column["data"] in ["created_at", "updated_at"]:
                    search_dates = column["search"]["value"].split("~")
                    start_query = Q()
                    end_query = Q()

                    if search_dates[0]:
                        start_query = Q(**{column["data"] + "__gte": search_dates[0]})
                    if search_dates[1]:
                        end_query = Q(**{column["data"] + "__lte": search_dates[1]})

                    search_query = start_query & end_query
                elif column["data"] == "status":
                    search_query = Q(
                        **{column["data"] + "__exact": column["search"]["value"]}
                    )
                elif column["data"] == "comment":
                    search_query = Q(
                        **{column["data"] + "__contains": column["search"]["value"]}
                    )
                else:
                    search_query = Q(
                        **{column["data"] + "__startswith": column["search"]["value"]}
                    )

                search_params.append(search_query)
                hint.append(column["data"])

        if order:
            order_by = query_columns[order.get("column")]["data"]

            hint.append(order_by)

            if order.get("dir") == "desc":
                order_by = "-" + order_by

    if search:
        if search["value"]:
            overall_search = '"' + search["value"] + '"'

    if not include_children:
        search_params.append(Q(has_parent=False))

    # Now we can construct the actual query parameters
    query_params = reduce(lambda x, y: x & y, search_params, Q())
    query_set = query_set.filter(query_params)

    # And set the ordering
    if order_by:
        query_set = query_set.order_by(order_by)

    # Marshmallow treats [] as 'serialize nothing' which is not what we
    # want, so translate to None
    if requested_fields:
        query_set = query_set.only(*requested_fields)
    else:
        requested_fields = None

    # Mongo seems to prefer using only the ['parent', '<sort field>']
    # index, even when also filtering. So we have to help it pick the right index.
    # BUT pymongo will blow up if you try to use a hint with a text search.
    if overall_search:
        query_set = query_set.search_text(overall_search)
    else:
        real_hint = []

        if not include_children:
            real_hint.append("parent")

        if "created_at" in hint:
            real_hint.append("created_at")
        for index in ["command", "system", "instance_name", "status"]:
            if index in hint:
                real_hint.append(index)
                break
        real_hint.append("index")

        # Sanity check - if index is 'bad' just let mongo deal with it
        index_name = "_".join(real_hint)
        if index_name in Request.index_names():
            query_set = query_set.hint(index_name)

    result = [r for r in query_set[start : start + length]]

    return {
        "requests": SchemaParser.serialize_request(
            result, only=requested_fields, many=True
        ),
        "length": len(result),
        "filtered_count": query_set.count(),  # This is another query
        "total_count": Request.objects.count(),
    }


@publish_event(Events.REQUEST_CREATED)
def process_request(request, wait_timeout=-1):
    """Validates and publishes a Request.

    Args:
        request: The Request
        wait_timeout: Float describing amount of time to wait for request to complete
            <0: Wait forever
            0: Don't wait at all
            >0: Wait this long

    Returns:
        The processed Request
    """
    # Validates the request based on what is in the database.
    # This includes the validation of the request parameters,
    # systems are there, commands are there etc.
    request = beer_garden.application.request_validator.validate_request(request)

    # Once validated we need to save since validate can modify the request
    request.save()
    request_id = str(request.id)

    if wait_timeout != 0:
        request_map[request_id] = Event()

    try:
        logger.info(f"Publishing request {request_id}")
        beer_garden.application.clients["pika"].publish_request(
            request, confirm=True, mandatory=True
        )
    except Exception as ex:
        # An error publishing means this request will never complete, so remove it
        request.delete()

        raise RequestPublishException(
            f"Error while publishing request {request.id} to queue "
            f"{request.system}[{request.system_version}]-{request.instance_name}"
        ) from ex

    # Metrics
    request_created(request)

    # Wait for the request to complete, if requested
    if wait_timeout != 0:
        if wait_timeout < 0:
            wait_timeout = None

        try:
            completed = request_map[request_id].wait(timeout=wait_timeout)
            if not completed:
                raise TimeoutError(f"Timeout exceeded for request {request_id}")

            request.reload()
        finally:
            request_map.pop(request_id, None)

    return request


def update_request(request_id, patch):
    status = None
    output = None
    error_class = None

    request = Request.objects.get(id=request_id)

    for op in patch:
        if op.operation == "replace":
            if op.path == "/status":
                if op.value.upper() in Request.STATUS_LIST:
                    if op.value.upper() == "IN_PROGRESS":
                        return start_request(request)
                    else:
                        status = op.value
                else:
                    raise ModelValidationError(f"Unsupported status value '{op.value}'")
            elif op.path == "/output":
                output = op.value
            elif op.path == "/error_class":
                error_class = op.value
            else:
                raise ModelValidationError(f"Unsupported path '{op.path}'")
        else:
            raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    return complete_request(request, status, output, error_class)


@publish_event(Events.REQUEST_STARTED)
def start_request(request):
    if request.status in Request.COMPLETED_STATUSES:
        raise ModelValidationError("Cannot update a completed request")

    request.status = "IN_PROGRESS"
    request.save()

    # Metrics
    request_started(request)

    return request


@publish_event(Events.REQUEST_COMPLETED)
def complete_request(request, status, output=None, error_class=None):
    if request.status in Request.COMPLETED_STATUSES:
        raise ModelValidationError("Cannot update a completed request")

    # Completing should always have a status
    request.status = status

    request.output = output
    request.error_class = error_class
    request.save()

    if str(request.id) in request_map:
        request_map[str(request.id)].set()

    # Metrics
    request_completed(request)

    return request


def cancel_request(request):
    if request.status in Request.COMPLETED_STATUSES:
        raise ModelValidationError("Cannot cancel a completed request")

    request.status = "CANCELED"
    request.save()

    # TODO - Metrics here?

    return request
