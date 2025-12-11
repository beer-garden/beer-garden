import asyncio

from brewtils.models import Operation, Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler


class EventPublisherAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def post(self):
        """
        ---
        summary: Publish a new event
        requestBody:
          name: event
          description: The the Event object
          content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Event'
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
        responses:
          204:
            description: An Event has been published
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Event
        """
        self.minimum_permission = Permissions.OPERATOR.name
        event = SchemaParser.parse_event(self.request.decoded_body, from_string=True)
        self.verify_user_permission_for_object(event)

        asyncio.create_task(
            self.process_operation(
                Operation(
                    operation_type="PUBLISH_EVENT", model=event, model_type="Event"
                ),
                filter_results=False,
            )
        )

        self.set_status(204)
