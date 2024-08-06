from brewtils.models import Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.events import publish
from beer_garden.metrics import collect_metrics


class EventPublisherAPI(AuthorizationHandler):
    parser = SchemaParser()

    @collect_metrics(transaction_type="API", group="EventPublisherAPI")
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
        self.minimum_permission = Permissions.OPERATOR.name
        event = SchemaParser.parse_event(self.request.decoded_body, from_string=True)
        self.verify_user_permission_for_object(event)
        publish(event)

        self.set_status(204)
