import json

import beer_garden.bg_utils
from beer_garden.bg_utils.mongo.models import Request
from beer_garden.api.brew_view.authorization import authenticated, Permissions
from beer_garden.api.brew_view.base_handler import BaseHandler
from beer_garden.api.brew_view.thrift import ThriftClient
from brewtils.errors import ModelValidationError, RequestPublishException
from brewtils.schema_parser import SchemaParser


class RequestAPI(BaseHandler):
    @authenticated(permissions=[Permissions.REQUEST_READ])
    async def get(self, namespace, request_id):
        """
        ---
        summary: Retrieve a specific Request
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ThriftClient() as client:
            thrift_response = await client.getRequest(namespace, request_id)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

    @authenticated(permissions=[Permissions.REQUEST_UPDATE])
    async def patch(self, namespace, request_id):
        """
        ---
        summary: Partially update a Request
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operation supported is `replace`, with
          paths `/status`, `/output`, and `/error_class`:
          ```JSON
          {
            "operations": [
              { "operation": "replace", "path": "/status", "value": "" }
            ]
          }
          ```
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ThriftClient() as client:
            try:
                thrift_response = await client.updateRequest(
                    namespace, request_id, self.request.decoded_body
                )
            except beer_garden.bg_utils.bg_thrift.InvalidRequest as ex:
                raise ModelValidationError(ex.message)

        self.write(thrift_response)


class RequestListAPI(BaseHandler):

    parser = SchemaParser()

    @authenticated(permissions=[Permissions.REQUEST_READ])
    async def get(self, namespace):
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
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        columns_arg = self.get_query_arguments("columns")
        order_arg = self.get_query_argument("order", default=None)
        search_arg = self.get_query_argument("search", default=None)
        child_arg = self.get_query_argument("include_children", default="")

        thrift_args = {
            "columns": [json.loads(c) for c in columns_arg],
            "order": json.loads(order_arg) if order_arg else None,
            "search": json.loads(search_arg) if search_arg else None,
            "include_children": bool(child_arg.lower() == "true"),
            "start": int(self.get_argument("start", default=0)),
            "length": int(self.get_argument("length", default=100)),
        }

        serialized_args = json.dumps(thrift_args)

        async with ThriftClient() as client:
            raw_response = await client.getRequests(namespace, serialized_args)

        parsed_response = json.loads(raw_response)

        response_headers = {
            # These are a courtesy for non-datatables requests. We want people
            # making a request with no headers to realize they probably aren't
            # getting the full dataset
            "start": thrift_args["start"],
            "length": parsed_response["length"],
            # And these are required by datatables
            "recordsFiltered": parsed_response["filtered_count"],
            "recordsTotal": parsed_response["total_count"],
            "draw": self.get_argument("draw", ""),
        }

        for key, value in response_headers.items():
            self.add_header(key, value)
            self.add_header("Access-Control-Expose-Headers", key)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(parsed_response["requests"])

    @authenticated(permissions=[Permissions.REQUEST_CREATE])
    async def post(self, namespace):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
            description: Maximum time (seconds) to wait for request completion
            type: integer
            default: None (Wait forever)
        consumes:
          - application/json
          - application/x-www-form-urlencoded
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
        else:
            raise ModelValidationError("Unsupported or missing content-type header")

        if self.current_user:
            request_model.requester = self.current_user.username

        wait_timeout = 0
        if self.get_argument("blocking", default="").lower() == "true":
            wait_timeout = self.get_argument("timeout", default=-1)

            # Also don't publish latency measurements
            self.request.ignore_latency = True

        async with ThriftClient() as client:
            try:
                thrift_response = await client.processRequest(
                    namespace,
                    self.parser.serialize_request(request_model),
                    float(wait_timeout),
                )
            except beer_garden.bg_utils.bg_thrift.InvalidRequest as ex:
                raise ModelValidationError(ex.message)
            except beer_garden.bg_utils.bg_thrift.PublishException as ex:
                raise RequestPublishException(ex.message)

        processed_request = self.parser.parse_request(thrift_response, from_string=True)

        self.set_status(201)
        self.write(self.parser.serialize_request(processed_request, to_string=False))

    def _parse_form_request(self):
        args = {"parameters": {}}

        for key, value in self.request.body_arguments.items():
            decoded_param = value[0].decode(self.request.charset)

            if key.startswith("parameters."):
                args["parameters"][key.replace("parameters.", "")] = decoded_param
            else:
                args[key] = decoded_param

        return Request(**args)
