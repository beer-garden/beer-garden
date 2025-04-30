# -*- coding: utf-8 -*-
import json

from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.models import Subscriber as BrewtilsSubscriber
from brewtils.models import Topic
from brewtils.schema_parser import SchemaParser
from mongoengine.queryset.visitor import Q

import beer_garden.db.api as db
from beer_garden.api.http.handlers import AuthorizationHandler


class TopicAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self, topic_id):
        """
        ---
        summary: Get a topic by id
        parameters:
          - name: topic_id
            in: path
            required: true
            description: The id of the Topic
            type: string
        responses:
          200:
            description: List of topic states
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

        response = await self.process_operation(
            Operation(operation_type="TOPIC_READ", kwargs={"topic_id": topic_id})
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self, topic_id):
        """
        ---
        summary: Delete a topic
        parameters:
          - name: topic_id
            in: path
            required: true
            description: The id of the topic
            type: string
        responses:
          200:
            description: List of topic states
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

        await self.process_operation(
            Operation(operation_type="TOPIC_DELETE", kwargs={"topic_id": topic_id})
        )

        self.set_status(204)

    async def patch(self, topic_id):
        """
        ---
        summary: Partially update a Topic
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * add
          * remove
          * reset_count

          ```JSON
          [
            { "operation": "add", "value": {subscriber} }
            { "operation": "remove", "value": {subscriber} }
            { "operation": "reset_count", "value": {subscriber} }
          ]
          ```
        parameters:
          - name: topic_id
            in: path
            required: true
            description: The id of the Topic
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Topic
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Topic with the given name
            schema:
              $ref: '#/definitions/Topic'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()
            subscriber = BrewtilsSubscriber(**op.value) if op.value else None

            if operation == "add":
                response = await self.process_operation(
                    Operation(
                        operation_type="TOPIC_ADD_SUBSCRIBER",
                        kwargs={"topic_id": topic_id, "subscriber": subscriber},
                    )
                )

            elif operation == "remove":
                response = await self.process_operation(
                    Operation(
                        operation_type="TOPIC_REMOVE_SUBSCRIBER",
                        kwargs={"topic_id": topic_id, "subscriber": subscriber},
                    )
                )

            elif operation == "reset_count":
                response = await self.process_operation(
                    Operation(
                        operation_type="TOPIC_RESET_COUNT",
                        kwargs={"topic_id": topic_id, "subscriber": subscriber},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class TopicNameAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self, topic_name):
        """
        ---
        summary: Get a topic_name by id
        parameters:
          - name: topic_name
            in: path
            required: true
            description: The name of the Topic
            type: string
        responses:
          200:
            description: List of topic states
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

        response = await self.process_operation(
            Operation(operation_type="TOPIC_READ", kwargs={"topic_name": topic_name})
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self, topic_name):
        """
        ---
        summary: Delete a topic
        parameters:
          - name: topic_name
            in: path
            required: true
            description: The name of the topic
            type: string
        responses:
          200:
            description: List of topic states
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

        await self.process_operation(
            Operation(operation_type="TOPIC_DELETE", kwargs={"topic_name": topic_name})
        )

        self.set_status(204)

    async def patch(self, topic_name):
        """
        ---
        summary: Partially update a Topic
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * add
          * remove

          ```JSON
          [
            { "operation": "add", "value": {subscriber} }
            { "operation": "remove", "value": {subscriber} }
          ]
          ```
        parameters:
          - name: topic_name
            in: path
            required: true
            description: The name of the Topic
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Topic
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Topic with the given name
            schema:
              $ref: '#/definitions/Topic'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()
            subscriber = BrewtilsSubscriber(**op.value)

            if operation == "add":
                response = await self.process_operation(
                    Operation(
                        operation_type="TOPIC_ADD_SUBSCRIBER",
                        kwargs={"topic_name": topic_name, "subscriber": subscriber},
                    )
                )

            elif operation == "remove":
                response = await self.process_operation(
                    Operation(
                        operation_type="TOPIC_REMOVE_SUBSCRIBER",
                        kwargs={"topic_name": topic_name, "subscriber": subscriber},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class TopicListAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self):
        """
        ---
        summary: Retrieve a page of all Topics
        description: |
          This endpoint queries multiple topics at once. Because it's intended to be
          used with Datatables the query parameters are ... complicated. Here are
          things to keep in mind:

          * With no query parameters this endpoint will return the first 100
            topics. This can be controlled by passing the `start` and `length` query
            parameters.

          To filter, search, and order you need to conform to how Datatables structures
          its query parameters.

          * To indicate fields that should be included in the response specify multiple
          `columns` query parameters:
          ```JSON
          {
            "data": "name",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value":"","regex":false}
          }
          {
            "data": "subscribers",
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
            "data": "name",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value": "topic1", "regex":false}
          }
          ```

          * To query on empty values, in the value use 'NOT' to return
            values that match ''
          `columns` query parameters:
          ```JSON
          {
            "data": "name",
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
            "data": "name",
            "name": "",
            "searchable": true,
            "orderable": true,
            "search": {"value":"NOT topic1","regex":false}
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
          - name: start
            in: query
            required: false
            description: The starting index for the page
            type: integer
          - name: length
            in: query
            required: false
            description: The maximum number of Topics to include in the page
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
            description: A page of Topics
            schema:
              type: array
              items:
                $ref: '#/definitions/Topic'
            headers:
              start:
                type: integer
                description: Echo of 'start' query parameter or '0'
              length:
                type: integer
                description: Number of Topics in the response
              draw:
                type: integer
                description: Echo of the 'draw' query parameter
              recordsFiltered:
                type: integer
                description: The number of Topics that satisfied the search filters
              recordsTotal:
                type: integer
                description: The total number of Topics
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

        if not self.get_query_arguments("columns"):
            response = await self.process_operation(
                Operation(operation_type="TOPIC_READ_ALL")
            )
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.write(response)
        else:
            # V1 API is a mess, it's basically written for datatables
            query_args = self._parse_datatables_parameters()

            q_filter = Q()
            q_filtered = None

            if query_args.get("q_filter"):
                query_args_q_filter = query_args["q_filter"]
                q_filtered = q_filter & query_args_q_filter
                query_args["q_filter"] = q_filtered
            else:
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

            topics = await self.process_operation(
                Operation(operation_type="TOPIC_READ_ALL", kwargs=query_args),
                serialize_kwargs=serialize_kwargs,
            )

            response_headers = {
                # These are for information
                "start": query_args["start"],
                "length": len(topics),
                # And these are required by datatables
                "recordsFiltered": db.count(
                    Topic,
                    q_filter=q_filtered if q_filtered else q_filter,
                    **query_args["filter_params"],
                ),
                "recordsTotal": db.count(Topic, q_filter=q_filter),
                "draw": self.get_argument("draw", ""),
            }

            for key, value in response_headers.items():
                self.add_header(key, value)
                self.add_header("Access-Control-Expose-Headers", key)

            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.write(json.dumps(topics))

    async def post(self):
        """
        ---
        summary: Create a new topic
        parameters:
          - name: topic
            in: body
            description: The Topic definition to create
            schema:
              $ref: '#/definitions/Topic'
        responses:
          201:
            description: A new Topic has been created
            schema:
              $ref: '#/definitions/Topic'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """
        topic = SchemaParser.parse_topic(self.request.decoded_body, from_string=True)

        response = await self.process_operation(
            Operation(
                operation_type="TOPIC_CREATE",
                args=[topic],
            )
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def patch(self):
        """
        ---
        summary: Request Topic Sync Updates
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:
          * sync_garden_topics
          * sync_all_topics
          ```JSON
          [
            { "operation": "sync_garden_topics", "value": {garden} }
            { "operation": "sync_all_topics"}
          ]
          ```
        parameters:
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Topic
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Successfully synced the topics
            schema:
              $ref: '#/definitions/Topic'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "sync_garden_topics":
                await self.process_operation(
                    Operation(
                        operation_type="TOPIC_SYNC_GARDEN",
                        kwargs={"garden_name": op.value},
                    )
                )

            elif operation == "sync_all_topics":
                await self.process_operation(
                    Operation(
                        operation_type="TOPIC_SYNC_GARDEN",
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_status(200)

    def _parse_datatables_parameters(self) -> dict:
        """Parse the HTTP datatables query parameters

        Returns:
            Dict of things to pass to the DB query:
                filter_params: Dict of filters
                include_fields: List of fields to include
                text_search: Text search field
                order_by: Ordering field

        """
        # These are what this function is populating
        filter_params = {}
        q_filter = Q()
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
        generated_arg = self.get_query_argument("include_generated", default="false")

        # And parse them into usable forms
        columns = [json.loads(c) for c in columns_arg]
        order = json.loads(order_arg)
        search = json.loads(search_arg)
        include_generated = bool(generated_arg.lower() == "true")

        # Cool, now we can do stuff
        if search and search["value"]:
            text_search = '"' + search["value"] + '"'

        if not include_generated:
            q_filter = q_filter & (
                Q(**{"subscribers__subscriber_type__in": ["ANNOTATED", "DYNAMIC"]})
                | Q(**{"subscribers__size": 0})
            )

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

                elif column["data"] == "subscribers":
                    q_filter = q_filter & (
                        Q(
                            **{
                                column["data"]
                                + "__garden__contains": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__namespace__contains": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__system__contains": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__version__contains": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__instance__contains": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__command__contains": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__consumer_count": column["search"]["value"]
                            }
                        )
                        | Q(
                            **{
                                column["data"]
                                + "__subscriber_type__contains": column["search"][
                                    "value"
                                ]
                            }
                        )
                    )

                elif column["search"]["value"].upper() in ["NOT", "NOT "]:
                    filter_params[column["data"] + "__exact"] = ""
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
            "q_filter": q_filter,
        }
