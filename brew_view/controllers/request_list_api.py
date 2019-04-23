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
from bg_utils.mongo.models import Request, System
from bg_utils.mongo.parser import MongoParser
from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brew_view.metrics import request_created, http_api_latency_total, request_latency
from brewtils.errors import (
    ConflictError,
    ModelValidationError,
    RequestPublishException,
    TimeoutExceededError,
)
from brewtils.models import Events


class RequestListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    indexes = [index["name"] for index in Request._meta["indexes"]]

    @authenticated(permissions=[Permissions.REQUEST_READ])
    def get(self):
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
        self.logger.debug("Getting Requests")

        query_set, requested_fields = self._get_query_set()

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
    def post(self):
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

        if request_model.parent:
            request_model.parent = Request.objects.get(id=str(request_model.parent.id))
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
        req = Request.objects.get(id=request_id)

        # Now attempt to add the instance status as a header.
        # The Request is already created at this point so it's a best-effort thing
        self.set_header("Instance-Status", "UNKNOWN")

        try:
            # Since request has system info we can query for a system object
            system = System.objects.get(name=req.system, version=req.system_version)

            # Loop through all instances in the system until we find the instance that
            # matches the request instance
            for instance in system.instances:
                if instance.name == req.instance_name:
                    self.set_header("Instance-Status", instance.status)

        # The Request is already created at this point so adding the Instance status
        # header is a best-effort thing
        except Exception as ex:
            self.logger.exception(
                "Unable to get Instance status for Request %s: %s", request_id, ex
            )

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

    def _get_query_set(self):
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

        query_set = Request.objects

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
