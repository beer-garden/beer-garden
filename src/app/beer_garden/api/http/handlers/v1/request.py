# -*- coding: utf-8 -*-
import base64
import gzip
import json
from asyncio import Future
from typing import Sequence

from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions, Request, System
from brewtils.schema_parser import SchemaParser

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.api.http.base_handler import future_wait
from beer_garden.api.http.exceptions import BadRequest, RequestForbidden
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.errors import UnknownGardenException
from beer_garden.metrics import collect_metrics
from beer_garden.requests import remove_bytes_parameter_base64


class RequestAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="RequestAPI")
    async def get(self, request_id):
        """
        ---
        summary: Retrieve a specific Request
        parameters:
          - name: request_id
            in: path
            required: true
            description: The ID of the Request
            type: string
        responses:
          200:
            description: Request with the given ID
            schema:
              $ref: '#/definitions/Request'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """

        _ = self.get_or_raise(Request, id=request_id)

        response = await self.process_operation(
            Operation(operation_type="REQUEST_READ", args=[request_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="RequestAPI")
    async def patch(self, request_id):
        """
        ---
        summary: Partially update a Request
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operation supported is `replace`, with
          paths `/status`, `/output`, and `/error_class`:
          ```JSON
          [
            { "operation": "replace", "path": "/status", "value": "" },
            { "operation": "replace", "path": "/output", "value": "" },
            { "operation": "replace", "path": "/error_class", "value": "" }
          ]
          ```
        parameters:
          - name: request_id
            in: path
            required: true
            description: The ID of the Request
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Request
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Request with the given ID
            schema:
              $ref: '#/definitions/Request'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        self.minimum_permission = Permissions.OPERATOR.name
        _ = self.get_or_raise(Request, id=request_id)

        operation = Operation(args=[request_id])
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            if op.operation == "replace":
                if op.path == "/status":
                    # If we get a start just assume there's no other op in patch
                    if op.value.upper() == "IN_PROGRESS":
                        operation.operation_type = "REQUEST_START"
                        operation.kwargs = {}
                        break

                    elif op.value.upper() in Request.COMPLETED_STATUSES:
                        operation.operation_type = "REQUEST_COMPLETE"
                        operation.kwargs["status"] = op.value

                    else:
                        raise ModelValidationError(
                            f"Unsupported status value '{op.value}'"
                        )

                elif op.path == "/output":
                    operation.kwargs["output"] = op.value

                elif op.path == "/error_class":
                    operation.kwargs["error_class"] = op.value

                else:
                    raise ModelValidationError(f"Unsupported path '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        response = await self.process_operation(operation)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class RequestOutputAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="RequestOutputAPI")
    async def get(self, request_id):
        """
        ---
        summary: Retrieve a specific Request output
        parameters:
          - name: request_id
            in: path
            required: true
            description: The ID of the Request
            type: string
        responses:
          200:
            description: Request output for request with the given ID
            type: String
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """

        _ = self.get_or_raise(Request, id=request_id)

        response = await self.process_operation(
            Operation(operation_type="REQUEST_READ", args=[request_id]),
            serialize_kwargs={"to_string": False},
        )

        if response["output"]:
            content_types = {
                "CSS": "text/css; charset=UTF-8",
                "HTML": "text/html; charset=UTF-8",
                "JS": "application/javascript; charset=UTF-8",
                "JSON": "application/json; charset=UTF-8",
                "STRING": "text/plain; charset=UTF-8",
                None: "text/plain; charset=UTF-8",
            }
            self.set_header("Content-Type", content_types[response["output_type"]])
            self.write(response["output"])
        else:
            self.set_status(204)


class RequestListAPI(AuthorizationHandler):
    parser = SchemaParser()

    @collect_metrics(transaction_type="API", group="RequestListAPI")
    async def get(self):
        """
        ---
        summary: Retrieve a page of all Requests
        description: |
          This endpoint queries multiple requests at once. Because it's intended to be
          used with Datatables the query parameters are ... complicated. Here are
          things to keep in mind:

          * With no query parameters this endpoint will return the first 100 non-child
            requests. This can be controlled by passing the `start` and `length` query
            parameters.

          * This endpoint does NOT return child request definitions. If you want to see
            child requests you must use the /api/v1/requests/{request_id} endpoint.

          * By default this endpoint also does not include child requests in the
            response. That is, if a request has a non-null `parent` field it will not
            be included in the response array. Use the `include_children` query
            parameter to change this behavior.

          To filter, search, and order you need to conform to how Datatables structures
          its query parameters.

          * To indicate fields that should be included in the response specify multiple
          `columns` query parameters:
          ```JSON
          {
            "data": "command",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value":"","regex":false}
          }
          {
            "data": "system",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value": "","regex": false}
          }
          ```
          * To filter a specific field set the value in the `search` key of its
            `column` definition:
          ```JSON
          {
            "data": "status",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value": "SUCCESS", "regex":false}
          }
          ```

          * To query on empty values, in the value use 'NOT' to return
            values that match ''
          `columns` query parameters:
          ```JSON
          {
            "data": "command",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value":"NOT","regex":false}
          }
          ```

          * To invert a field set match, in the value use the prefix 'NOT ' to return
            values that do not match that string value
          `columns` query parameters:
          ```JSON
          {
            "data": "command",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value":"NOT command","regex":false}
          }
          ```

          * To sort by a field use the `order` parameter. The `column` value should be
            the index of the column to sort and the `dir` value can be either "asc" or
            "desc."
          ```JSON
          {"column": 3,"dir": "asc"}
          ```

          * To perform a text-based search across all fields use the `search` parameter:
          ```JSON
          { "value": "SEARCH VALUE", "regex": false }
          ```
        parameters:
          - name: include_children
            in: query
            required: false
            description: |
                Flag indicating whether to include child requests in the response list
            type: boolean
            default: false
          - name: start
            in: query
            required: false
            description: The starting index for the page
            type: integer
          - name: length
            in: query
            required: false
            description: The maximum number of Requests to include in the page
            type: integer
            default: 100
          - name: draw
            in: query
            required: false
            description: Used by datatables, will be echoed in a response header
            type: integer
          - name: columns
            in: query
            required: false
            description: Datatables column definitions
            type: array
            collectionFormat: multi
            items:
              properties:
                data:
                  type: string
                name:
                  type: string
                searchable:
                  type: boolean
                  default: true
                orderable:
                  type: boolean
                  default: true
                search:
                  properties:
                    value:
                      type: string
                    regex:
                      type: boolean
                      default: false
          - name: search
            in: query
            required: false
            description: Datatables search object
            type: string
          - name: order
            in: query
            required: false
            description: Datatables order object
            type: string
        responses:
          200:
            description: A page of Requests
            schema:
              type: array
              items:
                $ref: '#/definitions/Request'
            headers:
              start:
                type: integer
                description: Echo of 'start' query parameter or '0'
              length:
                type: integer
                description: Number of Requests in the response
              draw:
                type: integer
                description: Echo of the 'draw' query parameter
              recordsFiltered:
                type: integer
                description: The number of Requests that satisfied the search filters
              recordsTotal:
                type: integer
                description: The total number of Requests
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """

        # V1 API is a mess, it's basically written for datatables
        query_args = self._parse_datatables_parameters()

        # Add the filter for only requests the user is permitted to see
        q_filter = self.permitted_objects_filter(Request)
        query_args["q_filter"] = q_filter

        # There are also some sane parameters
        query_args["start"] = self.get_argument("start", default="0")
        query_args["length"] = self.get_argument("length", default="100")

        # We want to get a list back from the DB so we can count the number of items
        serialize_kwargs = {"to_string": False}

        # If a field specification is provided it must also be passed to the serializer
        # Also, be aware that serialize_kwargs["only"] = [] means 'serialize nothing'
        if query_args.get("include_fields"):
            serialize_kwargs["only"] = query_args.get("include_fields")

        requests = await self.process_operation(
            Operation(operation_type="REQUEST_READ_ALL", kwargs=query_args),
            serialize_kwargs=serialize_kwargs,
        )

        response_headers = {
            # These are for information
            "start": query_args["start"],
            "length": len(requests),
            # And these are required by datatables
            "recordsFiltered": db.count(
                Request, q_filter=q_filter, **query_args["filter_params"]
            ),
            "recordsTotal": db.count(Request, q_filter=q_filter),
            "draw": self.get_argument("draw", ""),
        }

        for key, value in response_headers.items():
            self.add_header(key, value)
            self.add_header("Access-Control-Expose-Headers", key)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(requests))

    @collect_metrics(transaction_type="API", group="RequestListAPI")
    async def post(self):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: request
            in: body
            description: The Request definition
            schema:
              $ref: '#/definitions/Request'
          - name: blocking
            in: query
            required: false
            description: Flag indicating whether to wait for request completion
            type: boolean
            default: false
          - name: timeout
            in: query
            required: false
            description: Max seconds to wait for request completion. (-1 = wait forever)
            type: float
            default: -1
          - name: request
            in: formData
            required: false
            description: |
              For multipart/form-data requests (required when uploading a
              a file as a parameter) this field acts the same as the request (body)
              parameter and should be formatted per that field's definition.
            type: object
          - name: file_upload
            in: formData
            required: false
            type: file
            description: |
              A file to upload for use as input to a "bytes" type request
              parameter. NOTE: The name of the field in the submitted form data should
              match the name of the actual "bytes" type field that the command being
              tasked is expecting. The "file_upload" name is just a stand-in, since
              the actual expected name will vary for each command.
        consumes:
          - application/json
          - application/x-www-form-urlencoded
          - multipart/form-data
        responses:
          201:
            description: A new Request has been created
            schema:
              $ref: '#/definitions/Request'
            headers:
              Instance-Status:
                type: string
                description: |
                    Current status of the Instance that will process the
                    created Request
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        self.minimum_permission = Permissions.OPERATOR.name

        if self.request.mime_type == "application/json":
            request_model = self.parser.parse_request(
                self.request.decoded_body, from_string=True
            )
        elif self.request.mime_type == "application/x-www-form-urlencoded":
            request_model = self._parse_form_request()
        elif self.request.mime_type == "multipart/form-data":
            request_model = self._parse_multipart_form_data()
        else:
            raise ModelValidationError("Unsupported or missing content-type header")

        self.verify_user_permission_for_object(request_model)

        if (
            config.get("auth.enabled")
            and self.current_user
            and not request_model.requester
        ):
            request_model.requester = self.current_user.username

        wait_future = None
        if self.get_argument("blocking", default="").lower() == "true":
            wait_future = Future()

            # Also don't publish latency measurements
            self.request.ignore_latency = True

        try:
            created_request = await self.process_operation(
                Operation(
                    operation_type="REQUEST_CREATE",
                    model=request_model,
                    model_type="Request",
                    kwargs={"wait_event": wait_future},
                ),
                serialize_kwargs={"to_string": False},
            )
        except UnknownGardenException as ex:
            req_system = System(
                namespace=request_model.namespace,
                name=request_model.system,
                version=request_model.system_version,
            )
            raise ModelValidationError(
                f"Could not find a garden containing system {req_system}"
            ) from ex

        # Wait for the request to complete, if requested
        if wait_future:
            wait_timeout = float(self.get_argument("timeout", default="-1"))
            if wait_timeout < 0:
                wait_timeout = None

            await future_wait(wait_future, wait_timeout)

            if wait_future.exception():
                raise wait_future.exception()

            response = SchemaParser.serialize_request(wait_future.result())

        else:
            # We don't want to echo back the base64 encoding of any file parameters
            remove_bytes_parameter_base64(created_request["parameters"], False)
            response = SchemaParser.serialize_request(created_request)

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="RequestListAPI")
    async def put(self):
        """
        ---
        summary: Update a new Request
        parameters:
          - name: request
            in: body
            description: The Request definition
            schema:
              $ref: '#/definitions/Request'
        consumes:
          - application/json
        responses:
          201:
            description: A updated Request
            schema:
              $ref: '#/definitions/Request'
            headers:
              Instance-Status:
                type: string
                description: |
                    Current status of the Instance that will process the
                    created Request
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        self.minimum_permission = Permissions.OPERATOR.name
        request_model = self.parser.parse_request(
            (
                self.request.body.decode()
                if isinstance(self.request.body, bytes)
                else self.request.body
            ),
            from_string=True,
        )

        self.verify_user_permission_for_object(request_model)

        if (
            config.get("auth.enabled")
            and self.current_user
            and not request_model.requester
        ):
            request_model.requester = self.current_user.username

        try:
            update_request = await self.process_operation(
                Operation(
                    operation_type="REQUEST_UPDATE",
                    model=request_model,
                    model_type="Request",
                ),
                serialize_kwargs={"to_string": False},
            )
        except UnknownGardenException as ex:
            req_system = System(
                namespace=request_model.namespace,
                name=request_model.system,
                version=request_model.system_version,
            )
            raise ModelValidationError(
                f"Could not find a garden containing system {req_system}"
            ) from ex

        response = SchemaParser.serialize_request(update_request)

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="RequestListAPI")
    async def delete(self):
        """
        ---
        summary: Bulk delete or cancel of Requests
        parameters:
          - name: is_cancel
            in: query
            required: false
            description: |
                Is this a cancellation request
            type: bool
          - name: system
            in: query
            required: false
            description: |
                System Name
            type: string
          - name: system_version
            in: query
            required: false
            description: |
                System Version
            type: string
          - name: instance_name
            in: query
            required: false
            description: |
                Instance Name
            type: string
          - name: namespace
            in: query
            required: false
            description: |
                Namespace
            type: string
          - name: command
            in: query
            required: false
            description: |
                Command Name
            type: string
          - name: id
            in: query
            required: false
            description: |
                Request ID
            type: string
          - name: is_event
            in: query
            required: false
            description: |
                Is Event
            type: bool
          - name: output_type
            in: query
            required: false
            description: |
                Output Type
            type: string
          - name: status
            in: query
            required: false
            description: |
                Status
            type: string
          - name: command_type
            in: query
            required: false
            description: |
                Command Type
            type: string
          - name: hidden
            in: query
            required: false
            description: |
                Hidden
            type: bool
          - name: has_parent
            in: query
            required: false
            description: |
                Command Type
            type: bool
          - name: requester
            in: query
            required: false
            description: |
                Requester
            type: string
        responses:
          204:
            description: Requests has been successfully deleted
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name

        query_kwargs = {}
        global_check = True
        for supportedArg in [
            "system",
            "system_version",
            "instance_name",
            "namespace",
            "command",
            "id",
            "is_event",
            "output_type",
            "status",
            "command_type",
            "hidden",
            "has_parent",
            "requester",
        ]:
            value = self.get_argument(supportedArg, default=None)
            if value is not None:
                query_kwargs[supportedArg] = value
                if supportedArg in [
                    "system",
                    "system_version",
                    "instance_name",
                    "namespace",
                    "command",
                ]:
                    global_check = False

        # Either have global PLUGIN_ADMIN or access to specific filtering
        if global_check:
            self.verify_user_global_permission()
        else:
            check_kwargs = {}
            if "system" in query_kwargs:
                check_kwargs["system_name"] = query_kwargs["system"]
                check_kwargs["check_system"] = True
            if "system_version" in query_kwargs:
                check_kwargs["system_version"] = query_kwargs["system_version"]
                check_kwargs["check_version"] = True
            if "instance_name" in query_kwargs:
                check_kwargs["system_instances"] = [query_kwargs["instance_name"]]
                check_kwargs["check_instances"] = True
            if "namespace" in query_kwargs:
                check_kwargs["system_namespace"] = query_kwargs["namespace"]
                check_kwargs["check_namespace"] = True
            if "command" in query_kwargs:
                check_kwargs["system_name"] = query_kwargs["command"]
                check_kwargs["command_name"] = True

            if not self.modelFilter._checks(
                user=self.current_user,
                permission=self.minimum_permission,
                **check_kwargs,
            ):
                raise RequestForbidden

        await self.process_operation(
            Operation(
                operation_type=(
                    "REQUEST_CANCEL"
                    if self.get_argument("is_cancel", default=False)
                    else "REQUEST_DELETE"
                ),
                kwargs=query_kwargs,
            ),
            filter_results=False,
        )

        self.set_status(204)

    def _parse_form_request(self) -> Request:
        args = {"parameters": {}}

        for key, value in self.request.body_arguments.items():
            decoded_param = value[0].decode(self.request.charset)

            if key.startswith("parameters."):
                args["parameters"][key.replace("parameters.", "")] = decoded_param
            else:
                args[key] = decoded_param

        return Request(**args)

    def _parse_datatables_parameters(self) -> dict:
        """Parse the HTTP request's datatables query parameters

        Returns:
            Dict of things to pass to the DB query:
                filter_params: Dict of filters
                include_fields: List of fields to include
                text_search: Text search field
                order_by: Ordering field
                hint: The hint (index) to use

        """
        # These are what this function is populating
        filter_params = {}
        include_fields = []
        order_by = None
        text_search = None

        # These are internal helpers
        query_columns = []
        hint_helper = []

        # Start by pulling out the query parameters
        columns_arg = self.get_query_arguments("columns")
        order_arg = self.get_query_argument("order", default="{}")
        search_arg = self.get_query_argument("search", default="{}")
        child_arg = self.get_query_argument("include_children", default="false")
        hidden_arg = self.get_query_argument("include_hidden", default="false")

        # And parse them into usable forms
        columns = [json.loads(c) for c in columns_arg]
        order = json.loads(order_arg)
        search = json.loads(search_arg)
        include_children = bool(child_arg.lower() == "true")
        include_hidden = bool(hidden_arg.lower() == "true")

        # Cool, now we can do stuff
        if search and search["value"]:
            text_search = '"' + search["value"] + '"'

        if not include_children:
            filter_params["has_parent"] = False

        if not include_hidden:
            filter_params["hidden__ne"] = True

        for column in columns:
            query_columns.append(column)

            if column["data"]:
                if "__" in column["data"]:
                    include_fields.append(column["data"].split("__")[0])
                else:
                    include_fields.append(column["data"])

            if (
                "searchable" in column
                and column["searchable"]
                and column["search"]["value"]
            ):
                if "__" in column["data"]:
                    filter_params[column["data"]] = column["search"]["value"]
                elif column["data"] in ["created_at", "updated_at"]:
                    search_dates = column["search"]["value"].split("~")

                    if search_dates[0]:
                        filter_params[column["data"] + "__gte"] = search_dates[0]
                    if search_dates[1]:
                        filter_params[column["data"] + "__lte"] = search_dates[1]

                elif column["data"] == "status":
                    filter_params[column["data"] + "__exact"] = column["search"][
                        "value"
                    ]

                elif column["search"]["value"].upper() in ["NOT", "NOT "]:
                    filter_params[column["data"] + "__exact"] = ""
                elif column["data"] == "comment":
                    if column["search"]["value"].upper().startswith("NOT "):
                        filter_params[column["data"] + "__not__contains"] = column[
                            "search"
                        ]["value"][4:]
                    else:
                        filter_params[column["data"] + "__contains"] = column["search"][
                            "value"
                        ]

                else:
                    if column["search"]["value"].upper().startswith("NOT "):
                        filter_params[column["data"] + "__not__startswith"] = column[
                            "search"
                        ]["value"][4:]
                    else:
                        filter_params[column["data"] + "__startswith"] = column[
                            "search"
                        ]["value"]

                hint_helper.append(column["data"])

        if order:
            order_by = query_columns[order.get("column")]["data"]

            hint_helper.append(order_by)

            if order.get("dir") == "desc":
                order_by = "-" + order_by

        return {
            "filter_params": filter_params,
            "include_fields": include_fields,
            "text_search": text_search,
            "order_by": order_by,
            "hint": self._determine_hint(hint_helper, include_children, include_hidden),
        }

    @staticmethod
    def _determine_hint(
        hint_helper: Sequence[str], include_children: bool, include_hidden: bool
    ) -> str:
        """Function that will figure out correct index to use

        This is necessary since it seems that the ['parent', '<sort field>'] index is
        always used, even when also filtering.

        Args:
            hint_helper: List of relevant hint information
            include_children: Whether child requests are to be included
            include_hidden: Whether hidden requests are to be included

        Returns:
            The correct hint to use

        """
        real_hint = []

        if not include_hidden:
            real_hint.append("hidden")
        if not include_children:
            real_hint.append("parent")

        if "created_at" in hint_helper:
            real_hint.append("created_at")
        for index in ["command", "system", "instance_name", "status"]:
            if index in hint_helper:
                real_hint.append(index)
                break
        real_hint.append("index")

        return "_".join(real_hint)

    def _parse_multipart_form_data(self) -> Request:
        """Generate a Request object from multipart/form-data input"""
        request_form = self.get_body_argument("request")

        if request_form is None:
            raise BadRequest(
                reason="request parameter required for multipart/form-data requests"
            )

        try:
            request_form_dict = json.loads(request_form)
        except json.JSONDecodeError:
            raise BadRequest(reason="request parameter must be valid JSON")

        self._add_files_to_request(request_form_dict)

        return Request(**request_form_dict)

    def _add_files_to_request(self, request_form_dict: dict) -> None:
        """Processes any files attached to the request and adds them as parameters to
        the supplied request_form_dict representing the Request object that will be
        constructed.

        The files are base64 encoded and embedded into a parameter under the "base64"
        field. This allows for transport down to a child garden if necessary. The target
        garden, whether it be local or remote, will then convert this file data into a
        RawFile and replace "base64" with the an "id" reference field for final storage.
        """
        file_parameters = {}
        files = self.request.files

        for _file in files:
            file_contents = files[_file][0]["body"]

            file_parameters[_file] = {
                "type": "bytes",
                "base64": base64.b64encode(gzip.compress(file_contents)).decode(
                    "ascii"
                ),
            }

        request_form_dict["parameters"].update(file_parameters)
