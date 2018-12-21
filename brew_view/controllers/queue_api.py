import logging

from tornado.gen import coroutine

from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.models import Events


class QueueAPI(BaseHandler):

    logger = logging.getLogger(__name__)

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
        self.request.event.name = Events.QUEUE_CLEARED.name
        self.request.event.payload = {"queue_name": queue_name}

        with thrift_context() as client:
            yield client.clearQueue(queue_name)

        self.set_status(204)


class OldQueueAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    def delete(self, queue_name):
        """
        ---
        summary: Clear a queue by canceling all requests
        deprecated: true
        description: This endpoint is DEPRECATED - Use /api/v1/queues/{queue_name}
            instead.
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
          - Deprecated
        """
        self.redirect("/api/v1/queues/" + queue_name, permanent=True)
