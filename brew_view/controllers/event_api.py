import logging

from tornado.websocket import WebSocketHandler

import brew_view
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.base_handler import BaseHandler
from brewtils.schema_parser import SchemaParser


class EventPublisherAPI(BaseHandler):

    logger = logging.getLogger(__name__)
    parser = SchemaParser()

    def post(self):
        """
        ---
        summary: Publish a new notification
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
        publishers = self.get_query_arguments('publisher')

        if not publishers:
            brew_view.event_publishers.publish_event(event)
        else:
            for publisher in publishers:
                brew_view.event_publishers[publisher].publish_event(event)

        self.set_status(204)


class EventSocket(WebSocketHandler):

    logger = logging.getLogger(__name__)
    parser = BeerGardenSchemaParser()

    closing = False
    listeners = set()

    def check_origin(self, origin):
        return True

    def open(self):
        if EventSocket.closing:
            self.close(reason='Shutting down')
        else:
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
        EventSocket.closing = True

        for listener in cls.listeners:
            listener.close(reason='Shutting down')
