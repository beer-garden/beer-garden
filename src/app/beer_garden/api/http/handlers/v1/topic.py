# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions
from brewtils.models import Subscriber as BrewtilsSubscriber
from brewtils.schema_parser import SchemaParser
from mongoengine import Q

from beer_garden.api.http.base_handler import BaseHandler


class TopicAPI(BaseHandler):
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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """

        response = await self.client(
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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        await self.client(
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

          ```JSON
          [
            { "operation": "add", "value": {subscriber} }
            { "operation": "remove", "value": {subscriber} }
            { "operation": "reset_count", "value": {subscriber} }
          ]
          ```
        requestBody:
          name: patch
          description: Instructions for how to update the Topic
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        parameters:
          - name: topic_id
            in: path
            required: true
            description: The id of the Topic
            type: string
        responses:
          200:
            description: Topic with the given name
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()
            subscriber = BrewtilsSubscriber(**op.value) if op.value else None

            if operation == "add":
                response = await self.client(
                    Operation(
                        operation_type="TOPIC_ADD_SUBSCRIBER",
                        kwargs={"topic_id": topic_id, "subscriber": subscriber},
                    )
                )

            elif operation == "remove":
                response = await self.client(
                    Operation(
                        operation_type="TOPIC_REMOVE_SUBSCRIBER",
                        kwargs={"topic_id": topic_id, "subscriber": subscriber},
                    )
                )

            elif operation == "reset_count":
                response = await self.client(
                    Operation(
                        operation_type="TOPIC_RESET_COUNT",
                        kwargs={"topic_id": topic_id, "subscriber": subscriber},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class TopicNameAPI(BaseHandler):
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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """

        response = await self.client(
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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """

        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        await self.client(
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
        requestBody:
          name: patch
          description: Instructions for how to update the Topic
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        parameters:
          - name: topic_name
            in: path
            required: true
            description: The name of the Topic
            type: string
        responses:
          200:
            description: Topic with the given name
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()
            subscriber = BrewtilsSubscriber(**op.value)

            if operation == "add":
                response = await self.client(
                    Operation(
                        operation_type="TOPIC_ADD_SUBSCRIBER",
                        kwargs={"topic_name": topic_name, "subscriber": subscriber},
                    )
                )

            elif operation == "remove":
                response = await self.client(
                    Operation(
                        operation_type="TOPIC_REMOVE_SUBSCRIBER",
                        kwargs={"topic_name": topic_name, "subscriber": subscriber},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class TopicListAPI(BaseHandler):
    parser = SchemaParser()

    async def get(self):
        """
        ---
        summary: Retrieve topics
        parameters:
          - name: hide_generated
            in: path
            required: false
            description: Hide topics containing only GENERATED subscribers
            type: boolean
        responses:
          200:
            description: List of topics
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Topic'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """

        hide_generated = self.get_query_argument("hide_generated", None)
        if hide_generated is None:
            hide_generated = False
        else:
            hide_generated = bool(hide_generated.lower() == "true")

        if hide_generated:
            q_filter = Q()
            q_filter = q_filter & (
                Q(**{"subscribers__subscriber_type__in": ["ANNOTATED", "DYNAMIC"]})
                | Q(**{"subscribers__size": 0})
            )
            response = await self.client(
                Operation(
                    operation_type="TOPIC_READ_ALL", kwargs={"q_filter": q_filter}
                )
            )
        else:
            response = await self.client(Operation(operation_type="TOPIC_READ_ALL"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def post(self):
        """
        ---
        summary: Create a new topic
        requestBody:
          name: topic
          description: The Topic definition to create
          content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
        responses:
          201:
            description: A new Topic has been created
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        topic = SchemaParser.parse_topic(self.request.decoded_body, from_string=True)

        response = await self.client(
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
          * sync_all_topics
          ```JSON
          [
            { "operation": "sync_all_topics"}
          ]
          ```
        requestBody:
          name: patch
          description: Instructions for how to update the Topic
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        responses:
          200:
            description: Successfully synced the topics
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Topic'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Topics
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "sync_all_topics":
                await self.client(
                    Operation(
                        operation_type="TOPIC_SYNC",
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_status(200)
