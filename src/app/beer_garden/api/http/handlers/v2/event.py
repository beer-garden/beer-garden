import logging

import itertools
from tornado.web import HTTPError
from tornado.websocket import WebSocketHandler

from beer_garden.api.http.authorization import AuthMixin
from beer_garden.api.auth import Permissions, authenticated, check_permission
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.errors import RequestForbidden

logger = logging.getLogger(__name__)


class EventSocket(AuthMixin, WebSocketHandler):

    closing = False
    listeners = {}

    def __init__(self, *args, **kwargs):
        super(EventSocket, self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self, namespace):
        if EventSocket.closing:
            self.close(reason="Shutting down")
            return

        # We can't go though the 'normal' BaseHandler exception translation
        try:
            check_permission(self.current_user, [Permissions.EVENT_READ])
        except (HTTPError, RequestForbidden) as ex:
            self.close(reason=str(ex))
            return

        listeners = self.listeners.get(namespace, None)
        if not listeners:
            self.listeners[namespace] = set()

        self.listeners[namespace].add(self)

    def on_close(self):
        for listeners in self.listeners.values():
            listeners.discard(self)

    def on_message(self, message):
        pass

    @classmethod
    def publish(cls, namespace, message):
        # Don't bother if nobody is listening
        listeners = cls.listeners.get(namespace, set())
        if not len(listeners):
            return

        for listener in listeners:
            listener.write_message(message)

    @classmethod
    def shutdown(cls):
        logger.debug("Closing websocket connections")
        EventSocket.closing = True

        for listener in itertools.chain(cls.listeners.values()):
            listener.close(reason="Shutting down")


class EventPublisherAPI(BaseHandler):
    @authenticated(permissions=[Permissions.EVENT_CREATE])
    def post(self, namespace):
        """
        ---
        summary: Publish a new event
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
          - name: event
            in: body
            description: The the Event object
            schema:
              $ref: '#/definitions/Event'
        responses:
          204:
            description: An Event has been published
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Events
        """
        EventSocket.publish(namespace, self.request.decoded_body)

        self.set_status(204)
