# -*- coding: utf-8 -*-
import base64
import gzip
import json
from asyncio import Event
from typing import Sequence

from brewtils.errors import ModelValidationError, TimeoutExceededError
from brewtils.models import Operation
from brewtils.models import Request as BrewtilsRequest
from brewtils.models import System as BrewtilsSystem
from brewtils.schema_parser import SchemaParser

import beer_garden.db.api as db
from beer_garden.api.authorization import Permissions
from beer_garden.api.http.base_handler import event_wait
from beer_garden.api.http.exceptions import BadRequest
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.db.mongo.models import Request
from beer_garden.errors import UnknownGardenException
from beer_garden.requests import remove_bytes_parameter_base64

REQUEST_CREATE = Permissions.REQUEST_CREATE.value
REQUEST_READ = Permissions.REQUEST_READ.value
REQUEST_UPDATE = Permissions.REQUEST_UPDATE.value
REQUEST_DELETE = Permissions.REQUEST_DELETE.value


class RequestAPI(AuthorizationHandler):
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
        _ = self.get_or_raise(Request, REQUEST_READ, id=request_id)

        response = await self.client(
            Operation(operation_type="REQUEST_READ", args=[request_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

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
        _ = self.get_or_raise(Request, REQUEST_UPDATE, id=request_id)

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

                    elif op.value.upper() in BrewtilsRequest.COMPLETED_STATUSES:
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

        response = await self.client(operation)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class RequestOutputAPI(AuthorizationHandler):
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
        _ = self.get_or_raise(Request, REQUEST_READ, id=request_id)

        response = await self.client(
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
        q_filter = self.permitted_objects_filter(Request, REQUEST_READ)
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

        requests = await self.client(
            Operation(operation_type="REQUEST_READ_ALL", kwargs=query_args),
            serialize_kwargs=serialize_kwargs,
        )

        response_headers = {
            # These are for information
            "start": query_args["start"],
            "length": len(requests),
            # And these are required by datatables
            "recordsFiltered": db.count(
                BrewtilsRequest, q_filter=q_filter, **query_args["filter_params"]
            ),
            "recordsTotal": db.count(BrewtilsRequest, q_filter=q_filter),
            "draw": self.get_argument("draw", ""),
        }

        for key, value in response_headers.items():
            self.add_header(key, value)
            self.add_header("Access-Control-Expose-Headers", key)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(requests))

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
            required: true
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

        self.verify_user_permission_for_object(REQUEST_CREATE, request_model)

        if self.current_user:
            request_model.requester = self.current_user.username

        wait_event = None
        if self.get_argument("blocking", default="").lower() == "true":
            wait_event = Event()

            # Also don't publish latency measurements
            self.request.ignore_latency = True

        try:
            created_request = await self.client(
                Operation(
                    operation_type="REQUEST_CREATE",
                    model=request_model,
                    model_type="Request",
                    kwargs={"wait_event": wait_event},
                ),
                serialize_kwargs={"to_string": False},
            )
        except UnknownGardenException as ex:
            req_system = BrewtilsSystem(
                namespace=request_model.namespace,
                name=request_model.system,
                version=request_model.system_version,
            )
            raise ModelValidationError(
                f"Could not find a garden containing system {req_system}"
            ) from ex

        # Wait for the request to complete, if requested
        if wait_event:
            wait_timeout = float(self.get_argument("timeout", default="-1"))
            if wait_timeout < 0:
                wait_timeout = None

            if not await event_wait(wait_event, wait_timeout):
                raise TimeoutExceededError("Timeout exceeded")

            # Reload to get the completed request
            response = await self.client(
                Operation(operation_type="REQUEST_READ", args=[created_request["id"]])
            )
        else:
            # We don't want to echo back the base64 encoding of any file parameters
            remove_bytes_parameter_base64(created_request["parameters"], False)
            response = SchemaParser.serialize_request(created_request)

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    def _parse_form_request(self) -> BrewtilsRequest:
        args = {"parameters": {}}

        for key, value in self.request.body_arguments.items():
            decoded_param = value[0].decode(self.request.charset)

            if key.startswith("parameters."):
                args["parameters"][key.replace("parameters.", "")] = decoded_param
            else:
                args[key] = decoded_param

        return BrewtilsRequest(**args)

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
                include_fields.append(column["data"])

            if (
                "searchable" in column
                and column["searchable"]
                and column["search"]["value"]
            ):
                if column["data"] in ["created_at", "updated_at"]:
                    search_dates = column["search"]["value"].split("~")

                    if search_dates[0]:
                        filter_params[column["data"] + "__gte"] = search_dates[0]
                    if search_dates[1]:
                        filter_params[column["data"] + "__lte"] = search_dates[1]

                elif column["data"] == "status":
                    filter_params[column["data"] + "__exact"] = column["search"][
                        "value"
                    ]

                elif column["data"] == "comment":
                    filter_params[column["data"] + "__contains"] = column["search"][
                        "value"
                    ]

                else:
                    filter_params[column["data"] + "__startswith"] = column["search"][
                        "value"
                    ]

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

    def _parse_multipart_form_data(self) -> BrewtilsRequest:
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

        return BrewtilsRequest(**request_form_dict)

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
