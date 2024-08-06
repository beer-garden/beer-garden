# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden
from beer_garden.metrics import collect_metrics


class AdminAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="AdminAPI")
    async def patch(self):
        """
        ---
        summary: Initiate administrative actions
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
        parameters:
          - name: patch
            in: body
            required: true
            description: Instructions for operations
            schema:
              $ref: '#/definitions/Patch'
        responses:
          204:
            description: Operation successfully initiated
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Admin
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
