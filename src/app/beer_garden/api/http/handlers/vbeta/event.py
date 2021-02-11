from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class EventPublisherAPI(BaseHandler):

    parser = SchemaParser()

    async def post(self):
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

        event = SchemaParser.parse_event(self.request.decoded_body, from_string=True)

        await self.client(
            Operation(operation_type="PUBLISH_EVENT", model=event, model_type="Event"),
            serialize_kwargs={"to_string": False},
        )

        self.set_status(204)
