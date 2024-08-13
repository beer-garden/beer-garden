# -*- coding: utf-8 -*-
from asyncio import Future

from brewtils.errors import ModelValidationError, RequestProcessingError
from brewtils.models import Operation, Permissions, System
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import future_wait
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.metrics import collect_metrics


class InstanceAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="InstanceAPI")
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

        _ = self.get_or_raise(System, instances__id=instance_id)

        response = await self.process_operation(
            Operation(operation_type="INSTANCE_READ", args=[instance_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @collect_metrics(transaction_type="API", group="InstanceAPI")
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
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        _ = self.get_or_raise(System, instances__id=instance_id)

        await self.process_operation(
            Operation(operation_type="INSTANCE_DELETE", args=[instance_id])
        )

        self.set_status(204)

    @collect_metrics(transaction_type="API", group="InstanceAPI")
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
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        _ = self.get_or_raise(System, instances__id=instance_id)

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "initialize":
                runner_id = None
                if op.value:
                    runner_id = op.value.get("runner_id")

                response = await self.process_operation(
                    Operation(
                        operation_type="INSTANCE_INITIALIZE",
                        args=[instance_id],
                        kwargs={"runner_id": runner_id},
                    )
                )

            elif operation == "start":
                response = await self.process_operation(
                    Operation(operation_type="INSTANCE_START", args=[instance_id])
                )

            elif operation == "restart":
                response = await self.process_operation(
                    Operation(operation_type="INSTANCE_RESTART", args=[instance_id])
                )

            elif operation == "stop":
                response = await self.process_operation(
                    Operation(operation_type="INSTANCE_STOP", args=[instance_id])
                )

            elif operation == "heartbeat":
                response = await self.process_operation(
                    Operation(operation_type="INSTANCE_HEARTBEAT", args=[instance_id])
                )

            elif operation == "replace":
                if op.path.lower() == "/status":
                    response = await self.process_operation(
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
                    response = await self.process_operation(
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

    @collect_metrics(transaction_type="API", group="InstanceLogAPI")
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
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        _ = self.get_or_raise(System, instances__id=instance_id)

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

        self.set_header("request_id", response.id)
        self.set_header("Content-Type", "text/plain; charset=UTF-8")
        self.write(response.output if response.output else "")

    async def _generate_get_response(self, instance_id, start_line, end_line):
        wait_future = Future()

        response = await self.process_operation(
            Operation(
                operation_type="INSTANCE_LOGS",
                kwargs={
                    "instance_id": instance_id,
                    "wait_event": wait_future,
                    "start_line": start_line,
                    "end_line": end_line,
                },
            ),
            serialize_kwargs={"to_string": False},
        )

        wait_timeout = float(self.get_argument("timeout", default="15"))
        if wait_timeout < 0:
            wait_timeout = None
        await future_wait(wait_future, wait_timeout)

        if wait_future.exception():
            raise wait_future.exception()

        response = wait_future.result()

        if response.status == "ERROR":
            raise RequestProcessingError(response.output)

        return response


class InstanceQueuesAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="InstanceQueuesAPI")
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
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        _ = self.get_or_raise(System, instances__id=instance_id)

        response = await self.process_operation(
            Operation(operation_type="QUEUE_READ_INSTANCE", args=[instance_id]),
            filter_results=False,
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
