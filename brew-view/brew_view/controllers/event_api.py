import logging

import brew_view
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
