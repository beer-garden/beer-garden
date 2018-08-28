import logging

from tornado.gen import coroutine

from bg_utils.parser import BeerGardenSchemaParser
from brew_view import thrift_context
from brew_view.authorization import check_permission, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError


class AdminAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    @coroutine
    def patch(self):
        """
        ---
        summary: Initiate a rescan of the plugin directory
        description: |
          The body of the request needs to contain a set of instructions
          detailing the operations to perform.

          Currently the only operation supported is `rescan`:
          ```JSON
          {
            "operations": [
              { "operation": "rescan" }
            ]
          }
          ```
          * Will remove from the registry and database any currently stopped
            plugins who's directory has been removed.
          * Will add and start any new plugin directories.
        parameters:
          - name: patch
            in: body
            required: true
            description: Instructions for operations
            schema:
              $ref: '#/definitions/Patch'
        responses:
          204:
            description: Rescan successfully initiated
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Admin
        """
        operations = self.parser.parse_patch(
            self.request.decoded_body, many=True, from_string=True)

        for op in operations:
            if op.operation == 'rescan':
                check_permission(self.current_user, [Permissions.SYSTEM_CREATE])
                with thrift_context() as client:
                    yield client.rescanSystemDirectory()
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        self.set_status(204)


class OldAdminAPI(BaseHandler):

    @coroutine
    def post(self):
        """
        ---
        summary: Initiate a rescan of the plugin directory
        deprecated: true
        description: |
          This endpoint is DEPRECATED - Use PATCH /api/v1/admin instead.

          Will initiate a rescan of the plugins directory.
          * Will remove from the registry and database any currently stopped
            plugins who's directory has been removed.
          * Will add and start any new plugin directories.
        responses:
          204:
            description: Rescan successfully initiated
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        with thrift_context() as client:
            yield client.rescanSystemDirectory()

        self.set_status(204)
