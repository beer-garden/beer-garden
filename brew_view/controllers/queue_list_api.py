import logging

from tornado.gen import coroutine

from bg_utils.models import System
from bg_utils.parser import BeerGardenSchemaParser
from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.models import Events, Queue


class QueueListAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    @coroutine
    @authenticated(permissions=[Permissions.QUEUE_READ])
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
                $ref: '#/definitions/Queue'
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

                queue = Queue(name='UNKNOWN', system=system.name, version=system.version,
                              instance=instance.name, system_id=str(system.id),
                              display=system.display_name, size=-1)

                with thrift_context() as client:
                    try:
                        queue_info = yield client.getQueueInfo(system.name, system.version,
                                                               instance.name)
                        queue.name = queue_info.name
                        queue.size = queue_info.size
                    except Exception:
                        self.logger.error("Error getting queue size for %s[%s]-%s" %
                                          (system.name, instance.name, system.version))

                queues.append(queue)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(self.parser.serialize_queue(queues, to_string=True, many=True))

    @coroutine
    @authenticated(permissions=[Permissions.QUEUE_DELETE])
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
                $ref: '#/definitions/Queue'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        self.redirect('/api/v1/queues/', permanent=True)

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
        self.redirect('/api/v1/queues/', permanent=True)
