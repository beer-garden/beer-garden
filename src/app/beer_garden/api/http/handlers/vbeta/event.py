from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.events import publish


class EventPublisherAPI(BaseHandler):

    parser = SchemaParser()

    @authenticated(permissions=[Permissions.CREATE])
    def post(self):
        """
        ---
        summary: Publish a new event
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
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
          - Event
        """
        publish(SchemaParser.parse_event(self.request.decoded_body, from_string=True))

        self.set_status(204)
