# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError, RequestProcessingError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class InstanceAPI(BaseHandler):
    @authenticated(permissions=[Permissions.INSTANCE_READ])
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

        response = await self.client(
            Operation(operation_type="INSTANCE_READ", args=[instance_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.INSTANCE_DELETE])
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

        await self.client(
            Operation(operation_type="INSTANCE_DELETE", args=[instance_id])
        )

        self.set_status(204)

    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
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
                    Operation(
                        operation_type="INSTANCE_UPDATE",
                        args=[instance_id],
                        kwargs={"new_status": "RUNNING"},
                    )
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


class InstanceLogAPI(BaseHandler):

    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
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

        start_line = self.get_query_argument("start_line", default=None)

        if start_line == '':
            start_line = None
        elif start_line:
            start_line = int(start_line)

        end_line = self.get_query_argument("end_line", default=None)

        if end_line == '':
            end_line = None
        elif end_line:
            end_line = int(end_line)

        wait_timeout = float(self.get_query_argument("wait_timeout", default=-1))

        response = await self.client(
            Operation(
                operation_type="INSTANCE_LOGS",
                args=[instance_id],
                kwargs={'start_line': start_line,
                        'end_line': end_line,
                        'wait_timeout': wait_timeout}
            ),
            serialize_kwargs={"to_string": False},
        )

        if response["status"] == "ERROR":
            raise RequestProcessingError(response["output"])

        else:
            response = response["output"].replace('["', '').replace('"]', '').replace('", "', '').replace('\\n', '\n')
            self.set_header("Content-Type", "text/plain; charset=UTF-8")

        self.write(response)

    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
    async def delete(self, instance_id):
        """
        ---
        summary: Delete a specific Instance Log Config
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

        raise ModelValidationError(f"Unsupported operation")

    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
    async def patch(self, instance_id):
        """
        ---
        summary: Partially update an Instance Log Config
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

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
            description: Instructions for how to update the Instance Logs
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

        raise ModelValidationError(f"Unsupported operation")
