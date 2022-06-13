import beer_garden.config as config
from beer_garden.api.authorization import Permissions
from beer_garden.api.http.exceptions import BadRequest, NotFound, RoutingException
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.command_publishing_blocklist import (
    CommandPublishingBlocklistListInputSchema,
    CommandPublishingBlocklistSchema,
)
from beer_garden.command_publishing_blocklist import (
    command_publishing_blocklist_add,
    command_publishing_blocklist_delete,
)
from beer_garden.db.mongo.models import CommandPublishingBlocklist, Garden
from beer_garden.errors import RoutingRequestException

SYSTEM_UPDATE = Permissions.SYSTEM_UPDATE.value
SYSTEM_READ = Permissions.SYSTEM_READ.value


class CommandPublishingBlocklistPathAPI(AuthorizationHandler):
    def delete(self, command_publishing_id):
        """
        ---
        summary: Remove a command from event publishing block list
        parameters:
          - name: command_publishing_id
            in: path
            required: true
            description: id of entry in command publishing block list
            type: string
        responses:
          204:
            description: Command has been successfully removed from block list
            schema:
              $ref: '#/definitions/CommandPublishingBlocklist'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Command Block List
        """
        blocked_command = CommandPublishingBlocklist.objects.get(
            id=command_publishing_id
        )

        if blocked_command["namespace"] != config.get("garden.name"):
            target_garden = Garden.objects.get(
                namespaces__contains=blocked_command["namespace"],
                connection_type__nin=[None, "LOCAL"],
            )
        else:
            target_garden = Garden.objects.get(name=blocked_command["namespace"])
        self.verify_user_permission_for_object(SYSTEM_UPDATE, target_garden)

        try:
            command_publishing_blocklist_delete(blocked_command)
        except RoutingRequestException:
            raise RoutingException(
                reason=f"Could not route to child garden: {blocked_command['namespace']}"
            )

        self.set_status(204)


class CommandPublishingBlocklistAPI(AuthorizationHandler):
    def get(self):
        """
        ---
        summary: Retrieve list of commands in publishing block list
        responses:
          200:
            description: list of commands in publishing block list
            schema:
              $ref: '#/definitions/CommandPublishingBlocklistListSchema'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Command Block List
        """
        permitted_blocklist_entries = self.permissioned_queryset(
            CommandPublishingBlocklist, SYSTEM_READ
        )
        response = {
            "command_publishing_blocklist": CommandPublishingBlocklistSchema(many=True)
            .dump(permitted_blocklist_entries)
            .data
        }

        self.write(response)

    def post(self):
        """
        ---
        summary: Add a list of commands to event publishing block list
        parameters:
          - name: CommandPublishingBlocklist
            in: body
            description: The system, namespace and command name
            schema:
              $ref: '#/definitions/CommandPublishingBlocklistListInputSchema'
        consumes:
          - application/json
        responses:
          201:
            description: list of commands that have been added to publishing block list
            schema:
              $ref: '#/definitions/CommandPublishingBlocklistListSchema'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Command Block List
        """
        commands = self.schema_validated_body(CommandPublishingBlocklistListInputSchema)
        checked_gardens = []

        if len(commands["command_publishing_blocklist"]) == 0:
            raise BadRequest(reason="Empty list was submitted")

        for command in commands["command_publishing_blocklist"]:
            if command["namespace"] not in checked_gardens:
                try:
                    if command["namespace"] != config.get("garden.name"):
                        target_garden = Garden.objects.get(
                            namespaces__contains=command["namespace"],
                            connection_type__nin=[None, "LOCAL"],
                        )
                    else:
                        target_garden = Garden.objects.get(name=command["namespace"])
                    self.verify_user_permission_for_object(SYSTEM_UPDATE, target_garden)
                except NotFound:
                    raise BadRequest(
                        reason=f"Invalid garden name: {command['namespace']}"
                    )
                checked_gardens.append(command["namespace"])

        added_commands = []
        for command in commands["command_publishing_blocklist"]:
            try:
                blocked_command = command_publishing_blocklist_add(
                    command, return_value=True
                )
                added_commands.append(blocked_command)
            except RoutingRequestException:
                raise RoutingException(
                    reason=f"Could not route to child garden: {command['namespace']}"
                )

        response = {
            "command_publishing_blocklist": CommandPublishingBlocklistSchema(many=True)
            .dump(added_commands)
            .data
        }

        self.set_status(201)
        self.write(response)
