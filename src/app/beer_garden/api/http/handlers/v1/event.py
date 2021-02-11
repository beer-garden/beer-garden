# -*- coding: utf-8 -*-
import logging

from beer_garden.filters.permission_mapper import Permissions
from beer_garden.filters.model_filter import permission_check, model_filter
from brewtils.errors import RequestForbidden
from tornado.web import HTTPError
from tornado.websocket import WebSocketHandler
import beer_garden.config as config

from beer_garden.api.http.authorization import (
    AuthMixin,
    query_token_auth,
)
from brewtils.schema_parser import SchemaParser

logger = logging.getLogger(__name__)


class EventSocket(AuthMixin, WebSocketHandler):

    closing = False
    listeners = set()

    auth_providers = frozenset([query_token_auth])

    def check_origin(self, origin):
        return True

    def open(self):
        if EventSocket.closing:
            self.close(reason="Shutting down")
            return

        # We can't go though the 'normal' BaseHandler exception translation
        try:
            permission_check(
                current_user=self.current_user, required_permission=Permissions.READ
            )
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

        run_filter = config.get("auth").enabled

        for listener in cls.listeners:
            if run_filter and model_filter(
                SchemaParser.parse_event(message, from_string=True),
                current_user=listener.current_user,
                required_permission=Permissions.READ,
                raise_error=False,
            ):
                listener.write_message(message)

    @classmethod
    def shutdown(cls):
        logger.debug("Closing websocket connections")
        EventSocket.closing = True

        for listener in cls.listeners:
            listener.close(reason="Shutting down")
