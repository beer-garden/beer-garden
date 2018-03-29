import json
import logging
from functools import reduce

from mongoengine import Q
from tornado.gen import coroutine

import bg_utils
from bg_utils.models import Request
from bg_utils.models import System
from bg_utils.parser import BeerGardenSchemaParser
from brew_view import thrift_context
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError, RequestPublishException
from brewtils.models import Events


class RequestListAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    def get(self):
        """
        ---
        summary: Retrieve a page of all Requests
        description: |
          This endpoint queries multiple requests at once. Because it's intended to be used with
          Datatables the query parameters are ... complicated. Here are things to keep in mind:

          * With no query parameters this endpoint will return the first 100 non-child requests.
            This can be controlled by passing the `start` and `length` query parameters.

          * This endpoint does NOT return child request definitions. If you want to see child
            requests you must use the /api/v1/requests/{request_id} endpoint.

          * By default this endpoint also does not include child requests in the response. That
            is, if a request has a non-null `parent` field it will not be included in the response
            array. Use the `include_children` query parameter to change this behavior.

          To filter, search, and order you need to conform to how Datatables structures its query
          parameters.

          * To indicate fields that should be included in the response specify multiple `columns`
            query parameters:
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
          * To filter a specific field set the value in the `search` key of its `column` definition:
          ```JSON
          {
            "data": "status",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value": "SUCCESS", "regex":false}
          }
          ```

          * To sort by a field use the `order` parameter. The `column` value should be the index
            of the column to sort and the `dir` value can be either "asc" or "desc."
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
            description: Flag indicating whether to include child requests in the response list
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

        # We need to do the slicing on the query. This greatly reduces load time.
        start = int(self.get_argument('start', default=0))
        length = int(self.get_argument('length', default=100))
        requests, filtered_count, requested_fields = self._get_requests(start, start+length)

        # Sweet, we have data. Now setup some headers for the response
        response_headers = {
            # These are a courtesy for non-datatables requests. We want people making a request
            # with no headers to realize they probably aren't getting the full dataset
            'start': start,
            'length': len(requests),

            # And these are required by datatables
            'recordsFiltered': filtered_count,
            'recordsTotal': Request.objects.count(),
            'draw': self.get_argument('draw', '')
        }

        for key, value in response_headers.items():
            self.add_header(key, value)
            self.add_header('Access-Control-Expose-Headers', key)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(self.parser.serialize_request(requests, to_string=True, many=True,
                                                 only=requested_fields))

    @coroutine
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
                description: Current status of the Instance that will process the created Request
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        self.request.event.name = Events.REQUEST_CREATED.name

        if self.request.mime_type == 'application/json':
            request_model = self.parser.parse_request(self.request.decoded_body, from_string=True)
        elif self.request.mime_type == 'application/x-www-form-urlencoded':
            args = {'parameters': {}}
            for key, value in self.request.body_arguments.items():
                if key.startswith('parameters.'):
                    args['parameters'][key.replace('parameters.', '')] = value[0].decode(
                        self.request.charset)
                else:
                    args[key] = value[0].decode(self.request.charset)
            request_model = Request(**args)
        else:
            raise ModelValidationError('Unsupported or missing content-type header')

        if request_model.parent:
            request_model.parent = Request.objects.get(id=str(request_model.parent.id))

        with thrift_context() as client:
            try:
                request_model.save()
                yield client.processRequest(str(request_model.id))
                request_model.reload()
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
        req = Request.objects.get(id=str(request_model.id))

        # Now attempt to add the instance status as a header.
        # The Request is already created at this point so it's a best-effort thing
        self.set_header("Instance-Status", 'UNKNOWN')

        try:
            # Since request has system info we can query for a system object
            system = System.objects.get(name=req.system, version=req.system_version)

            # Loop through all instances in the system until we find the instance that matches
            # the request instance
            for instance in system.instances:
                if instance.name == req.instance_name:
                    self.set_header("Instance-Status", instance.status)

        # The Request is already created at this point so adding the Instance status header is a
        # best-effort thing
        except Exception as ex:
            self.logger.exception('Unable to get Instance status for Request %s: %s',
                                  str(request_model.id), ex)

        self.request.event_extras = {'request': req}

        self.set_status(201)
        self.write(self.parser.serialize_request(request_model, to_string=False))

    def _get_requests(self, start, end):
        """Get Requests matching the HTTP request query parameters.

        :return requests: The collection of requests
        :return requested_fields: The fields to be returned for each Request
        """
        search_params = []
        requested_fields = []
        order_by = None
        overall_search = None

        raw_columns = self.get_query_arguments('columns')
        if raw_columns:
            columns = []

            for raw_column in raw_columns:
                column = json.loads(raw_column)
                columns.append(column)

                if column['data']:
                    requested_fields.append(column['data'])

                    if column['data'] == 'system':
                        requested_fields.append('instance_name')

                if 'searchable' in column and column['searchable'] and column['search']['value']:
                    if column['data'] in ['created_at', 'updated_at']:
                        search_dates = column['search']['value'].split('~')

                        if search_dates[0]:
                            search_params.append(Q(**{column['data']+'__gte': search_dates[0]}))

                        if search_dates[1]:
                            search_params.append(Q(**{column['data']+'__lte': search_dates[1]}))
                    else:
                        search_query = Q(**{column['data']+'__contains': column['search']['value']})

                        # Little hacky but whatever, need this because we combine system and
                        # instance in the same column
                        if column['data'] == 'system':
                            search_query |= Q(instance_name__contains=column['search']['value'])

                        search_params.append(search_query)

            raw_order = self.get_query_argument('order', default=None)
            if raw_order:
                order = json.loads(raw_order)
                order_by = columns[order.get('column')]['data']
                if order.get('dir') == 'desc':
                    order_by = '-' + order_by

        raw_search = self.get_query_argument('search', default=None)
        if raw_search:
            search = json.loads(raw_search)
            if search['value']:
                overall_search = '"'+search['value']+'"'

        # Default to only top-level requests
        if self.get_query_argument('include_children', default='false').lower() != 'true':
            search_params.append(Q(parent__exists=False))

        requests = Request.objects(reduce(lambda x, y: x & y, search_params, Q()))
        filtered_count = requests.count()

        if requested_fields:
            requests = requests.only(*requested_fields)

        if overall_search:
            requests = requests.search_text(overall_search)

        if order_by:
            requests = requests.order_by(order_by)

        # We only return a slice of the requests.
        # This prevents object serialization on the server side from slowing everything down.
        return requests[start:end], filtered_count, requested_fields
