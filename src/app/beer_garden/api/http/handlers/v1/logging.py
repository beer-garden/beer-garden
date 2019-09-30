# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class LoggingConfigAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Get the plugin logging configuration
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
          - name: system_name
            in: query
            required: false
            description: Specific system name to get logging configuration
            type: string
        responses:
          200:
            description: Logging Configuration for system
            schema:
                $ref: '#/definitions/LoggingConfig'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Config
        """
        system_name = self.get_query_argument("system_name", default="")

        response = await self.client.get_plugin_log_config(
            self.request.namespace, system_name
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def patch(self):
        """
        ---
        summary: Reload the plugin logging configuration
        description: |
          The body of the request needs to contain a set of instructions detailing the
          operation to make. Currently supported operations are below:
          ```JSON
          {
            "operations": [
                { "operation": "reload" }
            ]
          }
          ```
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
          - name: patch
            in: body
            required: true
            description: Operation to perform
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Updated plugin logging configuration
            schema:
              $ref: '#/definitions/LoggingConfig'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Config
        """
        operations = SchemaParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "reload":
                response = await self.client.reload_plugin_log_config(
                    self.request.namespace
                )
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
