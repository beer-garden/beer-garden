# -*- coding: utf-8 -*-
import logging

from brewtils.errors import RequestForbidden
from tornado.web import HTTPError
from tornado.websocket import WebSocketHandler

logger = logging.getLogger(__name__)


class EventSocket(WebSocketHandler):

    closing = False
    listeners = set()

    def check_origin(self, origin):
        return True

    def open(self):
        if EventSocket.closing:
            self.close(reason="Shutting down")
            return

        # We can't go though the 'normal' BaseHandler exception translation
        try:
            # TODO: A permissions check for the old bg-read permission was here
            # This is likely not the appropriate place for the permission check, but
            # we should evaluate and then remove this bit if appropriate
            pass
        except (HTTPError, RequestForbidden) as ex:
            self.close(reason=str(ex))
            return

        EventSocket.listeners.add(self)

    def on_close(self):
        EventSocket.listeners.discard(self)

    def on_message(self, message):
        pass

    @classmethod
    def publish(cls, message):
        # Don't bother if nobody is listening
        if not len(cls.listeners):
            return

        for listener in cls.listeners:
            listener.write_message(message)

    @classmethod
    def shutdown(cls):
        logger.debug("Closing websocket connections")
        EventSocket.closing = True

        for listener in cls.listeners:
            listener.close(reason="Shutting down")
