# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler


class RunnerAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self, runner_id):
        """
        ---
        summary: Get a runner
        parameters:
          - name: runner_id
            in: path
            required: true
            description: The ID of the Runner
            type: string
        responses:
          200:
            description: List of runner states
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Runner'
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
          - Runners
        """

        response = await self.process_operation(
            Operation(operation_type="RUNNER_READ", kwargs={"runner_id": runner_id})
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self, runner_id):
        """
        ---
        summary: Delete a runner
        parameters:
          - name: runner_id
            in: path
            required: true
            description: The ID of the Runner
            type: string
        responses:
          200:
            description: List of runner states
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Runner'
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
          - Runners
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        response = await self.process_operation(
            Operation(
                operation_type="RUNNER_DELETE",
                kwargs={"runner_id": runner_id, "remove": True},
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def patch(self, runner_id):
        """
        ---
        summary: Partially update a Runner
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * start
          * stop

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        requestBody:
          name: patch
          description: Instructions for how to update the Runner
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        parameters:
          - name: runner_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
        responses:
          200:
            description: Runner with the given ID
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Runner'
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
          - Runners
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "start":
                response = await self.process_operation(
                    Operation(
                        operation_type="RUNNER_START", kwargs={"runner_id": runner_id}
                    )
                )

            elif operation == "stop":
                response = await self.client(
                    Operation(
                        operation_type="RUNNER_STOP",
                        kwargs={"runner_id": runner_id},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class RunnerListAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self):
        """
        ---
        summary: Retrieve runners
        responses:
          200:
            description: List of runner states
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Runner'
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
          - Runners
        """

        response = await self.process_operation(
            Operation(operation_type="RUNNER_READ_ALL")
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def patch(self):
        """
        ---
        summary: Update runners
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * reload

          ```JSON
          [
            { "operation": "reload", "path": "echo-3.0.0" }
          ]
          ```
        requestBody:
          name: patch
          description: Instructions for how to update the Runner
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        responses:
          200:
            description: Reloaded Runners
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Runner'
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
          - Runners
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "reload":
                response = await self.process_operation(
                    Operation(operation_type="RUNNER_RELOAD", kwargs={"path": op.path})
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
