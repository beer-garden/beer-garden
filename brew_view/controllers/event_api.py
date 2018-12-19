import logging

from tornado.web import HTTPError
from tornado.websocket import WebSocketHandler

import brew_view
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import (
    authenticated,
    check_permission,
    query_token_auth,
    AuthMixin,
    Permissions,
)
from brew_view.base_handler import BaseHandler
from brewtils.errors import RequestForbidden
from brewtils.schema_parser import SchemaParser


class EventPublisherAPI(BaseHandler):

    logger = logging.getLogger(__name__)
    parser = SchemaParser()

    @authenticated(permissions=[Permissions.EVENT_CREATE])
    def post(self):
        """
        ---
        summary: Publish a new event
        parameters:
          - name: event
            in: body
            description: The the Event object
            schema:
              $ref: '#/definitions/Event'
          - name: publisher
            in: query
            required: false
            description: Specific publisher to use
            type: array
            collectionFormat: multi
            items:
              properties:
                data:
                  type: string
        responses:
          204:
            description: An Event has been published
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Beta
        """
        event = self.parser.parse_event(self.request.decoded_body, from_string=True)
        publishers = self.get_query_arguments("publisher")

        if not publishers:
            brew_view.event_publishers.publish_event(event)
        else:
            for publisher in publishers:
                brew_view.event_publishers[publisher].publish_event(event)

        self.set_status(204)


class EventSocket(AuthMixin, WebSocketHandler):

    logger = logging.getLogger(__name__)
    parser = MongoParser()

    closing = False
    listeners = set()

    def __init__(self, *args, **kwargs):
        super(EventSocket, self).__init__(*args, **kwargs)

        self.auth_providers.append(query_token_auth)

    def check_origin(self, origin):
        return True

    def open(self):
        if EventSocket.closing:
            self.close(reason="Shutting down")
            return

        # We can't go though the 'normal' BaseHandler exception translation
        try:
            check_permission(self.current_user, [Permissions.EVENT_READ])
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
        cls.logger.debug("Closing websocket connections")
        EventSocket.closing = True

        for listener in cls.listeners:
            listener.close(reason="Shutting down")
