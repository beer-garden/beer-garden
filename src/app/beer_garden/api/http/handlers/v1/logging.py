# -*- coding: utf-8 -*-
import json

from beer_garden.router import Route_Type, Route_Class
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class LoggingConfigAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Get the plugin logging configuration
        parameters:
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

        response = await self.client(
            obj_id=system_name,
            route_class=Route_Class.LOGGING,
            route_type=Route_Type.READ,
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
          - Config
        """

        response = await self.client(
            brewtils_obj=SchemaParser.parse_patch(
                self.request.decoded_body, many=True, from_string=True
            ),
            route_class=Route_Class.LOGGING,
            route_type=Route_Type.UPDATE,
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
