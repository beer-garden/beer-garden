# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.models import Subscriber as BrewtilsSubscriber
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.metrics import collect_metrics


class TopicAPI(BaseHandler):
    parser = SchemaParser()

    @collect_metrics(transaction_type="API", group="TopicAPI")
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

        response = await self.client(
            Operation(operation_type="TOPIC_READ", kwargs={"topic_id": topic_id})
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="TopicAPI")
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

        await self.client(
            Operation(operation_type="TOPIC_DELETE", kwargs={"topic_id": topic_id})
        )

        self.set_status(204)

    @collect_metrics(transaction_type="API", group="TopicAPI")
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
            subscriber = BrewtilsSubscriber(**op.value)

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
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
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
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

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

    @collect_metrics(transaction_type="API", group="TopicListAPI")
    async def get(self):
        """
        ---
        summary: Retrieve topics
        responses:
          200:
            description: List of topics
            schema:
              $ref: '#/definitions/Topic'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Topics
        """

        response = await self.client(Operation(operation_type="TOPIC_READ_ALL"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="TopicListAPI")
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

        response = await self.client(
            Operation(
                operation_type="TOPIC_CREATE",
                args=[topic],
            )
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
