import logging

from tornado.gen import coroutine

from bg_utils.models import System
from bg_utils.parser import BeerGardenSchemaParser
from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Events


class SystemAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.SYSTEM_READ])
    def get(self, system_id):
        """
        ---
        summary: Retrieve a specific System
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: include_commands
            in: query
            required: false
            description: Include the System's commands in the response
            type: boolean
            default: true
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.logger.debug("Getting System: %s", system_id)

        include_commands = self.get_query_argument(
            'include_commands', default='true').lower() != 'false'
        self.write(self.parser.serialize_system(System.objects.get(id=system_id), to_string=False,
                                                include_commands=include_commands))

    @coroutine
    @authenticated(permissions=[Permissions.SYSTEM_DELETE])
    def delete(self, system_id):
        """
        Will give Bartender a chance to remove instances of this system from the registry but will
        always delete the system regardless of whether the Bartender operation succeeds.
        ---
        summary: Delete a specific System
        description: Will remove instances of local plugins from the registry, clear and remove
            message queues, and remove the system from the database.
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
        responses:
          204:
            description: System has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.request.event.name = Events.SYSTEM_REMOVED.name
        self.request.event_extras = {'system': System.objects.get(id=system_id)}

        with thrift_context() as client:
            yield client.removeSystem(str(system_id))

        self.set_status(204)

    @coroutine
    @authenticated(permissions=[Permissions.SYSTEM_UPDATE])
    def patch(self, system_id):
        """
        ---
        summary: Partially update a System
        description: |
          The body of the request needs to contain a set of instructions detailing the updates to
          apply.
          Currently supported operations are below:
          ```JSON
          {
            "operations": [
              { "operation": "replace", "path": "/commands", "value": "" },
              { "operation": "replace", "path": "/description", "value": "new description"},
              { "operation": "replace", "path": "/display_name", "value": "new display name"},
              { "operation": "replace", "path": "/icon_name", "value": "new icon name"},
              { "operation": "update", "path": "/metadata", "value": {"foo": "bar"}}
            ]
          }
          ```
          Where `value` is a list of new Commands.
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the System
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.request.event.name = Events.SYSTEM_UPDATED.name

        system = System.objects.get(id=system_id)
        operations = self.parser.parse_patch(self.request.decoded_body, many=True, from_string=True)

        for op in operations:
            if op.operation == 'replace':
                if op.path == '/commands':
                    new_commands = self.parser.parse_command(op.value, many=True)
                    if system.has_different_commands(new_commands):
                        if system.commands and 'dev' not in system.version:
                            raise ModelValidationError('System %s-%s already exists with '
                                                       'different commands' %
                                                       (system.name, system.version))
                        else:
                            system.upsert_commands(new_commands)
                elif op.path in ['/description', '/icon_name', '/display_name']:
                    if op.value is None:
                        # If we set an attribute to None, mongoengine marks that attribute
                        # for deletion, so we don't do that.
                        value = ""
                    else:
                        value = op.value
                    attr = op.path.strip("/")
                    self.logger.debug("Updating system %s" % attr)
                    self.logger.debug("Old: %s" % getattr(system, attr))
                    setattr(system, attr, value)
                    self.logger.debug("Updated: %s" % getattr(system, attr))
                    system.save()
                else:
                    error_msg = "Unsupported path '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError('value', error_msg)
            elif op.operation == 'update':
                if op.path == '/metadata':
                    self.logger.debug("Updating system metadata")
                    self.logger.debug("Old: %s" % system.metadata)
                    system.metadata.update(op.value)
                    self.logger.debug("Updated: %s" % system.metadata)
                    system.save()
                else:
                    error_msg = "Unsupported path for update '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError('path', error_msg)
            elif op.operation == 'reload':
                with thrift_context() as client:
                    yield client.reloadSystem(system_id)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError('value', error_msg)

        system.reload()

        self.request.event_extras = {'system': system, 'patch': operations}

        self.write(self.parser.serialize_system(system, to_string=False))
