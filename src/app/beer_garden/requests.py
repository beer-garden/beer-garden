# -*- coding: utf-8 -*-
"""Request Service

The request service is responsible for:

* Validating requests
* Request completion notification
"""

import base64
import gzip
import json
import logging
import re
import threading
from builtins import str
from copy import deepcopy
from typing import Dict, List, Sequence, Union

import pika.spec
import six
import urllib3
from brewtils.choices import parse
from brewtils.errors import (
    ConflictError,
    ModelValidationError,
    RequestPublishException,
    RequestStatusTransitionError,
)
from brewtils.models import Choices, Events, Operation, Request, RequestTemplate, System
from requests import Session

import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.db.mongo.models import RawFile
from beer_garden.errors import NotUniqueException
from beer_garden.events import publish_event
from beer_garden.metrics import request_completed, request_created, request_started

logger = logging.getLogger(__name__)

request_map: Dict[str, threading.Event] = {}


class RequestValidator(object):
    """Class responsible for validating Requests"""

    _instance = None

    def __init__(self, validator_config):
        self.logger = logging.getLogger(__name__)

        self._command_timeout = validator_config.dynamic_choices.command.timeout

        self._session = Session()
        if not validator_config.dynamic_choices.url.ca_verify:
            urllib3.disable_warnings()
            self._session.verify = False
        elif validator_config.dynamic_choices.url.ca_cert:
            self._session.verify = validator_config.dynamic_choices.url.ca_cert

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls(config.get("request_validation"))
        return cls._instance

    def validate_request(self, request):
        """Validation to be called before you save a request from a user

        :param request: The request to validate
        """
        self.logger.debug("Validating request")

        system = self.get_and_validate_system(request)
        command = self.get_and_validate_command_for_system(request, system)
        request.parameters = self.get_and_validate_parameters(request, command)

        self.validate_parent_status(request)

        return request

    def validate_parent_status(self, request):
        """Ensure that a Request's parent request hasn't already completed.

        :param request: The request to validate
        :raises ConflictError: The parent request has already completed
        """
        if request.parent and request.parent.status in Request.COMPLETED_STATUSES:
            raise ConflictError("Parent request has already completed")

    def get_and_validate_system(self, request):
        """Ensure there is a system in the DB that corresponds to this Request.

        :param request: The request to validate
        :return: The system corresponding to this Request
        :raises ModelValidationError: There is no system that corresponds to this Request
        """
        system = db.query_unique(
            System,
            namespace=request.namespace,
            name=request.system,
            version=request.system_version,
        )
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
                request.hidden = command.hidden

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

        Note: It is significant that we build the parameters as a separate object and
        then assign it. This is significant because when you are setting a value to
        None, mongoengine interprets this as "mark the item for deletion" meaning that
        when you save that attribute, it will actually get deleted. Sounds weird right?
        Well at least you didn't have to troubleshoot it.

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
            command_parameters = command.parameters or []

        if request_parameters is None:
            request_parameters = request.parameters or {}

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
                    raw_allowed = choices.value
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
                        # Mongoengine stores None keys as 'null', use instead of None
                        key_reference_value = request.parameters.get(key) or "null"

                    raw_allowed = choices.value.get(key_reference_value)
                    if raw_allowed is None:
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

                raw_allowed = json.loads(
                    self._session.get(parsed_value["address"], params=query_params).text
                )
            elif choices.type == "command":

                if isinstance(choices.value, six.string_types):
                    parsed_value = parse(choices.value, parse_as="func")

                    choices_request = Request(
                        system=request.system,
                        system_version=request.system_version,
                        instance_name=request.instance_name,
                        namespace=request.namespace,
                        command=parsed_value["name"],
                        parameters=map_param_values(parsed_value["args"]),
                    )
                elif isinstance(choices.value, dict):
                    parsed_value = parse(choices.value["command"], parse_as="func")
                    choices_request = Request(
                        system=choices.value.get("system"),
                        system_version=choices.value.get("version"),
                        namespace=choices.value.get(
                            "namespace", config.get("garden.name")
                        ),
                        instance_name=choices.value.get("instance_name", "default"),
                        command=parsed_value["name"],
                        parameters=map_param_values(parsed_value["args"]),
                    )
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Choices value"
                        " must be a string or dictionary " % command_parameter.key
                    )

                try:
                    response = process_wait(choices_request, self._command_timeout)
                except TimeoutError:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Choices "
                        "request took too long to complete" % command_parameter.key
                    )

                raw_allowed = json.loads(response.output)

                if isinstance(raw_allowed, list):
                    if len(raw_allowed) < 1:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Result "
                            "of choices query was empty list" % command_parameter.key
                        )
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

            # At this point raw_allowed is a list, but that list can potentially contain
            # {"value": "", "text": ""} dicts. Need to collapse those to strings
            allowed_values = []
            for allowed in raw_allowed:
                if isinstance(allowed, dict):
                    allowed_values.append(allowed["value"])
                else:
                    allowed_values.append(allowed)

            if command_parameter.multi:
                for single_value in value:
                    if single_value not in allowed_values:
                        raise ModelValidationError(
                            "Value '%s' is not a valid choice for parameter with key "
                            "'%s'. Valid choices are: %s"
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
                    "%s was specified as a list, but was not provided as such"
                    % command_parameter.key
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
        """If the parameter is required but was not provided in the request_parameters
        and does not have a default, then raise a ValidationError"""
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
        """Validate that all the parameters passed in were valid keys. If there is a key
        specified that is not noted in the database, then a validation error is thrown"""
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
            elif parameter.type.upper() in ("ANY", "BASE64", "BYTES"):
                return value
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


def get_request(request_id: str = None, request: Request = None) -> Request:
    """Retrieve an individual Request

    Args:
        request_id: The Request ID
        request: The Request

    Returns:
        The Request

    """
    request = request or db.query_unique(Request, id=request_id, raise_missing=True)
    request.children = db.query(Request, filter_params={"parent": request})

    return request


def get_requests(**kwargs) -> List[Request]:
    """Search for Requests

    Args:
        kwargs: Parameters to be passed to the DB query

    Returns:
        The list of Requests that matched the query

    """
    return db.query(Request, **kwargs)


def _publish_request(request: Request, is_admin: bool, priority: int):
    """Publish a Request"""
    queue.put(
        request,
        is_admin=is_admin,
        priority=priority,
        confirm=True,
        mandatory=True,
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
    )


def _validate_request(request: Request):
    """Validates a Request"""
    return RequestValidator.instance().validate_request(request)


def process_request(
    new_request: Union[Request, RequestTemplate],
    wait_event: threading.Event = None,
    is_admin: bool = False,
    priority: int = 0,
) -> Request:
    """Validates and publishes a Request.

    Args:
        new_request: The Request
        wait_event: Event that will be added to the local event_map. Event will be set
        when the request completes.
        is_admin: Flag indicating this request should be published on the admin queue
        priority: Number between 0 and 1, inclusive. High numbers equal higher priority

    Returns:
        The processed Request

    """
    if type(new_request) == Request:
        request = new_request
    elif type(new_request) == RequestTemplate:
        request = Request.from_template(new_request)
    else:
        raise TypeError(
            f"new_request type is {type(new_request)}, expected "
            "brewtils.models.Request or brewtils.models.RequestTemplate,"
        )

    # Validation is only required for non Admin commands because Admin commands
    # are hard coded to map Plugin functions
    if not is_admin:
        try:
            request = _validate_request(request)
        except ModelValidationError:
            invalid_request(request)
            raise

    if request.command_type == "EPHEMERAL":
        logger.debug(f"Publishing {request!r}")
    else:
        # Save after validation since validate can modify the request
        request = create_request(request)

        logger.info(f"Publishing {request!r}")

        if wait_event:
            request_map[request.id] = wait_event

    try:
        _publish_request(request, is_admin=is_admin, priority=priority)
    except Exception as ex:
        # An error publishing means this request will never complete, so remove it
        if not request.command_type == "EPHEMERAL":
            db.delete(request)

            if wait_event:
                request_map.pop(request.id, None)

        raise RequestPublishException(
            f"Error while publishing {request!r} to message broker"
        ) from ex

    # Metrics
    request_created(request)

    return request


@publish_event(Events.REQUEST_CREATED)
def create_request(request: Request) -> Request:
    """Create a database entry (mongo Document based Request object) from a brewtils
    Request model object. Some transformations happen on a copy of the supplied Request
    prior to saving it to the database. The returned Request object is derived from this
    transformed copy, while the input Request object remains unmodified.

    Args:
        request: The brewtils Request object from which a database entry will be created

    Returns:
        Request: A brewtils Request model based on the newly created database entry.
            The parameters of the returned object may have been modified from the
            during processing of files in "bytes" type parameters.
    """
    # TODO: This deepcopy could be very memory intensive if the request contains large
    # file parameters. This should be revisited to see if there is a way to persist
    # remote requests locally without the base64 encoded data while avoiding this copy.
    request = deepcopy(request)
    replace_with_raw_file = request.namespace == config.get("garden.name")
    remove_bytes_parameter_base64(request.parameters, replace_with_raw_file)

    return db.create(request)


def remove_bytes_parameter_base64(
    parameters: dict, replace_with_raw_file: bool
) -> None:
    """Strips out the "base64" property of any parameters that are of type "bytes".
    Optionally can create a RawFile object from the "base64" and insert a reference
    to the RawFile.id in its place.

    This is done because the "base64" property is only used for transport of the
    request to remote gardens and is never intended to be persisted as an actual
    parameter.

    Args:
       parameters: A dict representing the request parameters
       replace_with_raw_file: If True, a RawFile will be created from the "base64" and
           an "id" reference to the RawFile will be inserted in place of "base64".

    Returns:
        None
    """
    for param in parameters:
        request_param = parameters[param]
        if isinstance(request_param, dict) and request_param.get("type") == "bytes":
            bytes_base64 = request_param.get("base64")

            if bytes_base64 is not None:
                if replace_with_raw_file:
                    raw_file = RawFile(
                        file=gzip.decompress(base64.b64decode(bytes_base64))
                    ).save()
                    request_param["id"] = str(raw_file.id)

                del request_param["base64"]


@publish_event(Events.REQUEST_STARTED)
def start_request(request_id: str = None, request: Request = None) -> Request:
    """Mark a Request as IN PROGRESS

    Args:
        request_id: The Request ID to start
        request: The Request to start

    Returns:
        The modified Request

    Raises:
        ModelValidationError: The Request is already completed

    """
    request = request or db.query_unique(Request, raise_missing=True, id=request_id)

    request.status = "IN_PROGRESS"
    request = db.update(request)

    # Metrics
    request_started(request)

    return request


@publish_event(Events.REQUEST_COMPLETED)
def complete_request(
    request_id: str = None,
    request: Request = None,
    status: str = None,
    output: str = None,
    error_class: str = None,
) -> Request:
    """Mark a Request as completed

    Args:
        request_id: The Request ID to complete
        request: The Request to complete
        status: The status to apply to the Request
        output: The output to apply to the Request
        error_class: The error class to apply to the Request

    Returns:
        The modified Request

    Raises:
        ModelValidationError: The Request is already completed

    """
    request = request or db.query_unique(Request, raise_missing=True, id=request_id)

    request.status = status
    request.output = output
    request.error_class = error_class

    request = db.update(request)

    # Metrics
    request_completed(request)

    return request


@publish_event(Events.REQUEST_CANCELED)
def cancel_request(request_id: str = None, request: Request = None) -> Request:
    """Mark a Request as CANCELED

    Args:
        request_id: The Request ID to cancel
        request: The Request to cancel

    Returns:
        The modified Request

    Raises:
        ModelValidationError: The Request is already completed

    """
    request = request or db.query_unique(Request, raise_missing=True, id=request_id)

    request.status = "CANCELED"
    request = db.update(request)

    # TODO - Metrics here?

    return request


@publish_event(Events.REQUEST_UPDATED)
def invalid_request(request: Request = None):
    request.status = "INVALID"
    return request


@publish_event(Events.REQUEST_UPDATED)
def update_request(request: Request):
    db.update(request)
    return request


def process_wait(request: Request, timeout: float) -> Request:
    """Helper to process a request and wait for completion using a threading.Event

    Args:
        request: Request to create
        timeout: Timeout used for wait

    Returns:
        The completed request
    """

    # We need a better solution for this. Because the Request library is imported
    # everywhere it causes issues when importing the router at the top because all of
    # the functions are not initialized. So we either leave this as is, or move the
    # requests import to the end of all of the files.
    import beer_garden.router as router

    req_complete = threading.Event()

    # Send the request through the router to allow for commands to work across Gardens
    created_request = router.route(
        Operation(
            operation_type="REQUEST_CREATE",
            model=request,
            model_type="Request",
            kwargs={"wait_event": req_complete},
        )
    )

    if not req_complete.wait(timeout):
        raise TimeoutError("Request did not complete before the specified timeout")

    return db.query_unique(Request, id=created_request.id)


def handle_event(event):
    # Whenever a request is completed check to see if this process is waiting for it
    if event.name == Events.REQUEST_COMPLETED.name:
        completion_event = request_map.pop(event.payload.id, None)
        if completion_event:
            completion_event.set()

    # Only care about local garden
    if event.garden == config.get("garden.name"):

        if event.name == Events.GARDEN_STOPPED.name:
            # When shutting down we need to close all handing connections/threads
            # waiting for a response. This will invoke each connection/thread to be
            # returned the current status of the Request.
            for request_event in request_map:
                request_map[request_event].set()

    # Only care about downstream garden
    elif event.garden != config.get("garden.name") and not event.error:
        if event.name in (
            Events.REQUEST_CREATED.name,
            Events.REQUEST_STARTED.name,
            Events.REQUEST_COMPLETED.name,
            Events.REQUEST_UPDATED.name,
            Events.REQUEST_CANCELED.name,
        ):
            # When we send child requests to child gardens where the parent was on
            # the local garden we remove the parent before sending them. Only setting
            # the subset of fields that change "corrects" the parent
            existing_request = db.query_unique(Request, id=event.payload.id)

            if existing_request:
                for field in ("status", "output", "error_class"):
                    setattr(existing_request, field, getattr(event.payload, field))

                try:
                    update_request(existing_request)
                except RequestStatusTransitionError:
                    pass
            else:
                # Attempt to create the request, if it already exists then continue on
                try:
                    db.create(event.payload)
                except NotUniqueException:
                    pass
