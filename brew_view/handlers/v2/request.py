import json
import logging

from datetime import timedelta
from functools import reduce
from mongoengine import Q
from tornado.gen import coroutine
from tornado.locks import Event
from tornado.util import TimeoutError

import bg_utils
import brew_view
from bg_utils.mongo.models import Job
from bg_utils.mongo.models import Request, System
from bg_utils.mongo.parser import MongoParser
from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brew_view.metrics import request_created, http_api_latency_total, request_latency
from brew_view.metrics import request_updated
from brewtils.errors import (
    ConflictError,
    ModelValidationError,
    RequestPublishException,
    TimeoutExceededError,
)
from brewtils.models import Events
from brewtils.models import Request as BrewtilsRequest


class RequestAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.REQUEST_READ])
    def get(self, namespace, request_id):
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
        req = Request.objects.get(id=str(request_id), namespace=namespace)
        req.children = Request.objects(parent=req, namespace=namespace)

        self.write(self.parser.serialize_request(req, to_string=False))

    @authenticated(permissions=[Permissions.REQUEST_UPDATE])
    def patch(self, namespace, request_id):
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
        req = Request.objects.get(id=request_id, namespace=namespace)
        operations = self.parser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )
        wait_event = None

        # We note the status before the operations, because it is possible for the
        # operations to update the status of the request. In that case, because the
        # updates are coming in in a single request it is okay to update the output or
        # error_class. Ideally this would be handled correctly when we better integrate
        # PatchOperations with their models.
        status_before = req.status

        for op in operations:
            if op.operation == "replace":
                if op.path == "/status":
                    if op.value.upper() in BrewtilsRequest.STATUS_LIST:
                        req.status = op.value.upper()

                        if op.value.upper() == "IN_PROGRESS":
                            self.request.event.name = Events.REQUEST_STARTED.name

                        elif op.value.upper() in BrewtilsRequest.COMPLETED_STATUSES:
                            self.request.event.name = Events.REQUEST_COMPLETED.name

                            if request_id in brew_view.request_map:
                                wait_event = brew_view.request_map[request_id]
                    else:
                        error_msg = "Unsupported status value '%s'" % op.value
                        self.logger.warning(error_msg)
                        raise ModelValidationError(error_msg)
                elif op.path == "/output":
                    if req.output == op.value:
                        continue

                    if status_before in Request.COMPLETED_STATUSES:
                        raise ModelValidationError(
                            "Cannot update output for a request "
                            "that is already completed"
                        )
                    req.output = op.value
                elif op.path == "/error_class":
                    if req.error_class == op.value:
                        continue

                    if status_before in Request.COMPLETED_STATUSES:
                        raise ModelValidationError(
                            "Cannot update error_class for a "
                            "request that is already completed"
                        )
                    req.error_class = op.value
                    self.request.event.error = True
                else:
                    error_msg = "Unsupported path '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        req.save()

        # Metrics
        request_updated(req, status_before)
        self._update_job_numbers(req, status_before)

        if wait_event:
            wait_event.set()

        self.request.event_extras = {"request": req, "patch": operations}

        self.write(self.parser.serialize_request(req, to_string=False))

    def _update_job_numbers(self, request, status_before):
        if (
            not request.metadata.get("_bg_job_id")
            or status_before == request.status
            or request.status not in Request.COMPLETED_STATUSES
        ):
            return

        try:
            job_id = request.metadata.get("_bg_job_id")
            document = Job.objects.get(id=job_id)
            if request.status == "ERROR":
                document.error_count += 1
            elif request.status == "SUCCESS":
                document.success_count += 1
            document.save()
        except Exception as exc:
            self.logger.warning("Could not update job counts.")
            self.logger.exception(exc)


class RequestListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    indexes = [index["name"] for index in Request._meta["indexes"]]

    @authenticated(permissions=[Permissions.REQUEST_READ])
    def get(self, namespace):
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
        query_set, requested_fields = self._get_query_set(namespace)

        # Actually execute the query. The slicing greatly reduces load time.
        start = int(self.get_argument("start", default=0))
        length = int(self.get_argument("length", default=100))
        requests = query_set[start : start + length]

        # Sweet, we have data. Now setup some headers for the response
        response_headers = {
            # These are a courtesy for non-datatables requests. We want people
            # making a request with no headers to realize they probably aren't
            # getting the full dataset
            "start": start,
            "length": len(requests),
            # And these are required by datatables
            "recordsFiltered": query_set.count(),  # This is another query
            "recordsTotal": Request.objects.count(),
            "draw": self.get_argument("draw", ""),
        }

        for key, value in response_headers.items():
            self.add_header(key, value)
            self.add_header("Access-Control-Expose-Headers", key)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            self.parser.serialize_request(
                requests, to_string=True, many=True, only=requested_fields
            )
        )

    @coroutine
    @authenticated(permissions=[Permissions.REQUEST_CREATE])
    def post(self, namespace):
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
        self.request.event.name = Events.REQUEST_CREATED.name

        if self.request.mime_type == "application/json":
            request_model = self.parser.parse_request(
                self.request.decoded_body, from_string=True
            )
        elif self.request.mime_type == "application/x-www-form-urlencoded":
            args = {"parameters": {}}
            for key, value in self.request.body_arguments.items():
                if key.startswith("parameters."):
                    args["parameters"][key.replace("parameters.", "")] = value[
                        0
                    ].decode(self.request.charset)
                else:
                    args[key] = value[0].decode(self.request.charset)
            request_model = Request(**args)
        else:
            raise ModelValidationError("Unsupported or missing content-type header")

        request_model.namespace = namespace

        if request_model.parent:
            request_model.parent = Request.objects.get(
                id=str(request_model.parent.id), namespace=namespace
            )
            if request_model.parent.status in Request.COMPLETED_STATUSES:
                raise ConflictError("Parent request has already completed")
            request_model.has_parent = True
        else:
            request_model.has_parent = False

        if self.current_user:
            request_model.requester = self.current_user.username

        # Ok, ready to save
        request_model.save()
        request_id = str(request_model.id)

        # Set up the wait event BEFORE yielding the processRequest call
        blocking = self.get_argument("blocking", default="").lower() == "true"
        if blocking:
            brew_view.request_map[request_id] = Event()

        with thrift_context() as client:
            try:
                yield client.processRequest(request_id)
            except bg_utils.bg_thrift.InvalidRequest as ex:
                request_model.delete()
                raise ModelValidationError(ex.message)
            except bg_utils.bg_thrift.PublishException as ex:
                request_model.delete()
                raise RequestPublishException(ex.message)
            except Exception:
                if request_model.id:
                    request_model.delete()
                raise

        # Query for request from body id
        req = Request.objects.get(id=request_id, namespace=namespace)

        self.request.event_extras = {"request": req}

        # Metrics
        request_created(request_model)

        if blocking:
            # Publish metrics and event here here so they aren't skewed
            # See https://github.com/beer-garden/beer-garden/issues/190
            self.request.publish_metrics = False
            http_api_latency_total.labels(
                method=self.request.method.upper(),
                route=self.prometheus_endpoint,
                status=self.get_status(),
            ).observe(request_latency(self.request.created_time))

            self.request.publish_event = False
            brew_view.event_publishers.publish_event(
                self.request.event, **self.request.event_extras
            )

            try:
                timeout = self.get_argument("timeout", default=None)
                delta = timedelta(seconds=int(timeout)) if timeout else None

                event = brew_view.request_map.get(request_id)

                yield event.wait(delta)

                request_model.reload()
            except TimeoutError:
                raise TimeoutExceededError(
                    "Timeout exceeded for request %s" % request_id
                )
            finally:
                brew_view.request_map.pop(request_id, None)

        self.set_status(201)
        self.write(self.parser.serialize_request(request_model, to_string=False))

    def _get_query_set(self, namespace):
        """Get Requests matching the HTTP request query parameters.

        :return query_set: The QuerySet representing this query
        :return requested_fields: The fields to be returned for each Request
        """
        search_params = []
        requested_fields = []
        order_by = None
        overall_search = None
        include_children = False
        hint = []

        raw_columns = self.get_query_arguments("columns")
        if raw_columns:
            columns = []

            for raw_column in raw_columns:
                column = json.loads(raw_column)
                columns.append(column)

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
                            start_query = Q(
                                **{column["data"] + "__gte": search_dates[0]}
                            )
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
                            **{
                                column["data"]
                                + "__startswith": column["search"]["value"]
                            }
                        )

                    search_params.append(search_query)
                    hint.append(column["data"])

            raw_order = self.get_query_argument("order", default=None)
            if raw_order:
                order = json.loads(raw_order)
                order_by = columns[order.get("column")]["data"]

                hint.append(order_by)

                if order.get("dir") == "desc":
                    order_by = "-" + order_by

        raw_search = self.get_query_argument("search", default=None)
        if raw_search:
            search = json.loads(raw_search)
            if search["value"]:
                overall_search = '"' + search["value"] + '"'

        # Default to only top-level requests
        if (
            self.get_query_argument("include_children", default="false").lower()
            != "true"
        ):
            search_params.append(Q(has_parent=False))
            include_children = True

        # And set the namespace
        search_params.append(Q(namespace=namespace))

        # Now we can construct the actual query parameters
        query_params = reduce(lambda x, y: x & y, search_params, Q())
        query_set = Request.objects.filter(query_params)

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

            if include_children:
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
            if index_name in self.indexes:
                query_set = query_set.hint(index_name)

        return query_set, requested_fields
