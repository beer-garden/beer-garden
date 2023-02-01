# -*- coding: utf-8 -*-
from asyncio import Event

from brewtils.errors import (
    ModelValidationError,
    RequestProcessingError,
    TimeoutExceededError,
)
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.authorization import Permissions
from beer_garden.api.http.base_handler import event_wait
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.db.mongo.models import System

INSTANCE_READ = Permissions.INSTANCE_READ.value
INSTANCE_UPDATE = Permissions.INSTANCE_UPDATE.value
QUEUE_READ = Permissions.QUEUE_READ.value


class InstanceAPI(AuthorizationHandler):
    async def get(self, instance_id):
        """
        ---
        summary: Retrieve a specific Instance
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        _ = self.get_or_raise(System, INSTANCE_READ, instances__id=instance_id)

        response = await self.client(
            Operation(operation_type="INSTANCE_READ", args=[instance_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self, instance_id):
        """
        ---
        summary: Delete a specific Instance
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
        responses:
          204:
            description: Instance has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        _ = self.get_or_raise(System, INSTANCE_UPDATE, instances__id=instance_id)

        await self.client(
            Operation(operation_type="INSTANCE_DELETE", args=[instance_id])
        )

        self.set_status(204)

    async def patch(self, instance_id):
        """
        ---
        summary: Partially update an Instance
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * initialize
          * start
          * stop
          * heartbeat
          * replace

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Instance
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        _ = self.get_or_raise(System, INSTANCE_UPDATE, instances__id=instance_id)

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "initialize":
                runner_id = None
                if op.value:
                    runner_id = op.value.get("runner_id")

                response = await self.client(
                    Operation(
                        operation_type="INSTANCE_INITIALIZE",
                        args=[instance_id],
                        kwargs={"runner_id": runner_id},
                    )
                )

            elif operation == "start":
                response = await self.client(
                    Operation(operation_type="INSTANCE_START", args=[instance_id])
                )

            elif operation == "stop":
                response = await self.client(
                    Operation(operation_type="INSTANCE_STOP", args=[instance_id])
                )

            elif operation == "heartbeat":
                response = await self.client(
                    Operation(operation_type="INSTANCE_HEARTBEAT", args=[instance_id])
                )

            elif operation == "replace":
                if op.path.lower() == "/status":
                    response = await self.client(
                        Operation(
                            operation_type="INSTANCE_UPDATE",
                            args=[instance_id],
                            kwargs={"new_status": op.value},
                        )
                    )
                else:
                    raise ModelValidationError(f"Unsupported path '{op.path}'")

            elif operation == "update":
                if op.path.lower() == "/metadata":
                    response = await self.client(
                        Operation(
                            operation_type="INSTANCE_UPDATE",
                            args=[instance_id],
                            kwargs={"metadata": op.value},
                        )
                    )
                else:
                    raise ModelValidationError(f"Unsupported path '{op.path}'")

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class InstanceLogAPI(AuthorizationHandler):
    async def get(self, instance_id):
        """
        ---
        summary: Retrieve a specific Instance
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
          - name: start_line
            in: query
            required: false
            description: Start line of logs to read from instance
            type: int
          - name: end_line
            in: query
            required: false
            description: End line of logs to read from instance
            type: int
          - name: timeout
            in: query
            required: false
            description: Max seconds to wait for request completion. (-1 = wait forever)
            type: float
            default: -1
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        _ = self.get_or_raise(System, INSTANCE_READ, instances__id=instance_id)

        start_line = self.get_query_argument("start_line", default=None)
        if start_line == "":
            start_line = None
        elif start_line:
            start_line = int(start_line)

        end_line = self.get_query_argument("end_line", default=None)
        if end_line == "":
            end_line = None
        elif end_line:
            end_line = int(end_line)

        response = await self._generate_get_response(instance_id, start_line, end_line)

        self.set_header("request_id", response["id"])
        self.set_header("Content-Type", "text/plain; charset=UTF-8")
        self.write(response["output"])

    async def _generate_get_response(self, instance_id, start_line, end_line):
        wait_event = Event()

        response = await self.client(
            Operation(
                operation_type="INSTANCE_LOGS",
                args=[instance_id],
                kwargs={
                    "wait_event": wait_event,
                    "start_line": start_line,
                    "end_line": end_line,
                },
            ),
            serialize_kwargs={"to_string": False},
        )

        wait_timeout = float(self.get_argument("timeout", default="15"))
        if wait_timeout < 0:
            wait_timeout = None
        if not await event_wait(wait_event, wait_timeout):
            raise TimeoutExceededError("Timeout exceeded")

        response = await self.client(
            Operation(operation_type="REQUEST_READ", args=[response["id"]]),
            serialize_kwargs={"to_string": False},
        )

        if response["status"] == "ERROR":
            raise RequestProcessingError(response["output"])

        return response


class InstanceQueuesAPI(AuthorizationHandler):
    async def get(self, instance_id):
        """
        ---
        summary: Retrieve queue information for instance
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The instance ID to pull queues for
            type: string
        responses:
          200:
            description: List of queue information objects for this instance
            schema:
              type: array
              items:
                $ref: '#/definitions/Queue'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        _ = self.get_or_raise(System, QUEUE_READ, instances__id=instance_id)

        response = await self.client(
            Operation(operation_type="QUEUE_READ_INSTANCE", args=[instance_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
