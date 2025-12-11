# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden


class AdminAPI(AuthorizationHandler):

    async def patch(self):
        """
        ---
        summary: Initiate administrative actions
        deprecated: true
        description: |
          The body of the request needs to contain a set of instructions
          detailing the operations to perform.

          Currently the supported operations are `rescan`:
          ```JSON
          [
            { "operation": "rescan" }
          ]
          ```
          * Will remove from the registry and database any currently stopped
            plugins who's directory has been removed.
          * Will add and start any new plugin directories.

          And reloading the plugin logging configuration:
          ```JSON
          [
            {
              "operation": "reload",
              "path": "/config/logging/plugin"
            }
          ]
          ```
        requestBody:
            name: patch
            description: Instructions for operations
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/PatchOperation'
        responses:
          204:
            description: Operation successfully initiated
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Deprecated
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name

        self.verify_user_permission_for_object(local_garden())

        operations = SchemaParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "rescan":
                await self.process_operation(Operation(operation_type="RUNNER_RESCAN"))
            elif op.operation == "reload":
                if op.path == "/config/logging/plugin":
                    await self.process_operation(
                        Operation(operation_type="PLUGIN_LOG_RELOAD")
                    )
                else:
                    raise ModelValidationError(f"Unsupported path '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_status(204)
