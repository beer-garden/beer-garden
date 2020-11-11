# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class LoggingAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Get plugin logging configuration
        description: |
          Will return a Python logging configuration that can be used to configure
          plugin logging.
        parameters:
          - name: local
            in: query
            required: false
            description: Whether to request the local plugin logging configuration
            type: boolean
            default: false
        responses:
          200:
            description: Logging Configuration for system
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Logging
        """
        local = self.get_query_argument("local", None)
        if local is None:
            local = False
        else:
            local = bool(local.lower() == "true")

        response = await self.client(
            Operation(operation_type="PLUGIN_LOG_READ", kwargs={"local": local})
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class LoggingConfigAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Get the plugin logging configuration
        deprecated: true
        parameters:
          - name: system_name
            in: query
            required: false
            description: UNUSED
            type: string
        responses:
          200:
            description: Logging Configuration for system
            schema:
                $ref: '#/definitions/LoggingConfig'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        response = await self.client(Operation(operation_type="PLUGIN_LOG_READ_LEGACY"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def patch(self):
        """
        ---
        summary: Reload the plugin logging configuration
        deprecated: true
        description: |
          The body of the request needs to contain a set of instructions detailing the
          operation to make. Currently supported operations are below:
          ```JSON
          { "operation": "reload" }
          ```
        parameters:
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
          - Deprecated
        """

        patch = SchemaParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        response = None
        for op in patch:
            if op.operation == "reload":
                response = await self.client(
                    Operation(operation_type="PLUGIN_LOG_RELOAD")
                )
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
