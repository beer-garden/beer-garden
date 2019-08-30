from beer_garden.brew_view.authorization import authenticated, Permissions
from beer_garden.brew_view.base_handler import BaseHandler
from beer_garden.brew_view.handlers.v2.event import EventSocket
from brewtils.schema_parser import SchemaParser


class EventPublisherAPI(BaseHandler):

    parser = SchemaParser()

    @authenticated(permissions=[Permissions.EVENT_CREATE])
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
        EventSocket.publish(self.request.namespace, self.request.decoded_body)

        self.set_status(204)
