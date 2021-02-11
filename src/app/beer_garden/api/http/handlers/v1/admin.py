# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class AdminAPI(BaseHandler):
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
        operations = SchemaParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "rescan":
                await self.client(Operation(operation_type="RUNNER_RESCAN"))
            elif op.operation == "reload":
                if op.path == "/config/logging/plugin":
                    await self.client(Operation(operation_type="PLUGIN_LOG_RELOAD"))
                else:
                    raise ModelValidationError(f"Unsupported path '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_status(204)
