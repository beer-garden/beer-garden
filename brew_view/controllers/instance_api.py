import logging
from datetime import datetime

from tornado.gen import coroutine

from bg_utils.models import Instance
from bg_utils.parser import BeerGardenSchemaParser
from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Events


class InstanceAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    event_dict = {
        'initialize': Events.INSTANCE_INITIALIZED.name,
        'start': Events.INSTANCE_STARTED.name,
        'stop': Events.INSTANCE_STOPPED.name
    }

    @authenticated(permissions=[Permissions.INSTANCE_READ])
    def get(self, instance_id):
        """
        ---
        summary: Retrieve a specific Instance
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        self.logger.debug("Getting Instance: %s", instance_id)

        self.write(self.parser.serialize_instance(Instance.objects.get(id=instance_id),
                                                  to_string=False))

    @coroutine
    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
    def patch(self, instance_id):
        """
        ---
        summary: Partially update an Instance
        description: |
          The body of the request needs to contain a set of instructions detailing the updates to
          apply. Currently the only operations are:

          * initialize
          * start
          * stop
          * heartbeat

          ```JSON
          {
            "operations": [
              { "operation": "" }
            ]
          }
          ```
        parameters:
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Instance
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        response = {}
        instance = Instance.objects.get(id=instance_id)
        operations = self.parser.parse_patch(self.request.decoded_body, many=True, from_string=True)

        for op in operations:
            if op.operation.lower() in ('initialize', 'start', 'stop'):
                self.request.event.name = self.event_dict[op.operation.lower()]
                with thrift_context() as client:
                    response = yield getattr(client, op.operation.lower()+'Instance')(instance_id)

            elif op.operation.lower() == 'heartbeat':
                instance.status_info.heartbeat = datetime.utcnow()
                instance.save()
                response = self.parser.serialize_instance(instance, to_string=False)

            elif op.operation.lower() == 'replace':
                if op.path.lower() == '/status':
                    if op.value.upper() == 'INITIALIZING':
                        self.request.event.name = Events.INSTANCE_INITIALIZED.name
                        with thrift_context() as client:
                            response = yield client.initializeInstance(instance_id)

                    elif op.value.upper() == 'STOPPING':
                        self.request.event.name = Events.INSTANCE_STOPPED.name
                        with thrift_context() as client:
                            response = yield client.stopInstance(instance_id)

                    elif op.value.upper() == 'STARTING':
                        self.request.event.name = Events.INSTANCE_STARTED.name
                        with thrift_context() as client:
                            response = yield client.startInstance(instance_id)

                    elif op.value.upper() in ['RUNNING', 'STOPPED']:
                        instance.status = op.value.upper()
                        instance.save()
                        response = self.parser.serialize_instance(instance, to_string=False)

                    else:
                        error_msg = "Unsupported status value '%s'" % op.value
                        self.logger.warning(error_msg)
                        raise ModelValidationError('value', error_msg)
                else:
                    error_msg = "Unsupported path '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError('value', error_msg)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError('value', error_msg)

        if self.request.event.name:
            self.request.event_extras = {'instance': instance}

        self.write(response)
