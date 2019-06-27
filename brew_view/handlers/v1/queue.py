import logging

from tornado.gen import coroutine

from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.models import Events

logger = logging.getLogger(__name__)


class QueueAPI(BaseHandler):
    @coroutine
    @authenticated(permissions=[Permissions.QUEUE_DELETE])
    def delete(self, queue_name):
        """
        ---
        summary: Clear a queue by canceling all requests
        parameters:
          - name: queue_name
            in: path
            required: true
            description: The name of the queue to clear
            type: string
        responses:
          204:
            description: Queue successfully cleared
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        with thrift_context() as client:
            yield client.clearQueue(queue_name)

        self.set_status(204)


class QueueListAPI(BaseHandler):
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
        logger.debug("Getting all queue info")

        with thrift_context() as client:
            queues = yield client.getAllQueueInfo()

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(queues)

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
        with thrift_context() as client:
            yield client.clearAllQueues()

        self.set_status(204)
