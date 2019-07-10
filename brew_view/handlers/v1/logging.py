from brew_view.base_handler import BaseHandler
from brew_view.thrift import ThriftClient
from brewtils.errors import ModelValidationError
from brewtils.schema_parser import SchemaParser


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

        async with ThriftClient() as client:
            thrift_response = await client.getPluginLogConfig(system_name)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

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
                async with ThriftClient() as client:
                    thrift_response = await client.reloadPluginLogConfig()
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)
