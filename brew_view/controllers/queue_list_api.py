import json
import logging

from tornado.gen import coroutine

from bg_utils.models import System
from brew_view import thrift_context
from brew_view.base_handler import BaseHandler
from brewtils.models import Events


class QueueListAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    @coroutine
    def get(self):
        """
        ---
        summary: Retrieve all queue information
        responses:
          200:
            description: List of all queue information objects
            schema:
              type: array
              items:
                properties:
                  system:
                    type: string
                  display:
                    type: string
                  version:
                    type: string
                  system_id:
                    type: string
                  instance:
                    type: string
                  name:
                    type: string
                  size:
                    type: integer
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        self.logger.debug("Getting all queues")

        queues = []
        systems = System.objects.all().select_related(max_depth=1)

        for system in systems:
            for instance in system.instances:

                queue = {
                    'system': system.name,
                    'display': system.display_name,
                    'version': system.version,
                    'system_id': str(system.id),
                    'instance': instance.name,
                }

                with thrift_context() as client:
                    try:
                        queue_info = yield client.getQueueInfo(system.name, system.version,
                                                               instance.name)
                        queue['name'] = queue_info.name
                        queue['size'] = queue_info.size
                    except Exception:
                        self.logger.error("Error getting queue size for %s[%s]-%s" %
                                          (system.name, instance.name, system.version))
                        queue['name'] = "UNKNOWN"
                        queue['size'] = "UNKNOWN"

                queues.append(queue)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(json.dumps(queues))

    @coroutine
    def delete(self):
        """
        ---
        summary: Cancel and clear all requests in all queues
        responses:
          204:
            description: All queues successfully cleared
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        self.request.event.name = Events.ALL_QUEUES_CLEARED.name

        with thrift_context() as client:
            yield client.clearAllQueues()

        self.set_status(204)


class OldQueueListAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    @coroutine
    def get(self):
        """
        ---
        summary: Retrieve all queue information
        deprecated: true
        description: This endpoint is DEPRECATED - Use /api/v1/queues instead.
        responses:
          200:
            description: List of all queue information objects
            schema:
              type: array
              items:
                properties:
                  system:
                    type: string
                  display:
                    type: string
                  version:
                    type: string
                  system_id:
                    type: string
                  instance:
                    type: string
                  name:
                    type: string
                  size:
                    type: integer
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        self.redirect('/api/v1/queues/', permanent=True)

    @coroutine
    def delete(self):
        """
        ---
        summary: Cancel and clear all requests in all queues
        deprecated: true
        description: This endpoint is DEPRECATED - Use /api/v1/queues instead.
        responses:
          204:
            description: All queues successfully cleared
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        self.request.event.name = Events.ALL_QUEUES_CLEARED.name

        with thrift_context() as client:
            yield client.clearAllQueues()

        self.set_status(204)
