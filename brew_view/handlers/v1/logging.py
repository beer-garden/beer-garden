import logging
import brew_view
from bg_utils.mongo.parser import MongoParser
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError

from tornado.gen import coroutine


class LoggingConfigAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    def get(self):
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
        system_name = self.get_query_argument("system_name", default=None)
        log_config = brew_view.plugin_logging_config.get_plugin_log_config(
            system_name=system_name
        )
        self.write(self.parser.serialize_logging_config(log_config, to_string=False))

    @coroutine
    def patch(self):
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
        operations = self.parser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "reload":
                brew_view.load_plugin_logging_config(brew_view.config)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError("value", error_msg)

        self.set_status(200)
        self.write(
            self.parser.serialize_logging_config(
                brew_view.plugin_logging_config, to_string=False
            )
        )
