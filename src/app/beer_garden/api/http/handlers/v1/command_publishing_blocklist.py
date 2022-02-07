from brewtils.models import Operation

import beer_garden.config as config
import beer_garden.router
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.db.mongo.models import CommandPublishingBlockList
from beer_garden.api.authorization import Permissions
from beer_garden.db.mongo.models import System


SYSTEM_UPDATE = Permissions.SYSTEM_UPDATE.value


class CommandPublishingBlockListPathAPI(AuthorizationHandler):
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
        blocked_command = CommandPublishingBlockList.objects.get(
            id=command_publishing_id
        )
        systems = System.objects(namespace=blocked_command["namespace"], name=blocked_command["system"])
        self.get_or_raise(System, SYSTEM_UPDATE, id=systems[0].id)

        if config.get("garden.name") != blocked_command["namespace"]:
            beer_garden.router.route(
                Operation(
                    operation_type="COMMAND_BLOCK_LIST_REMOVE",
                    args=[command_publishing_id],
                    target_garden_name=config.get("garden.name"),
                )
            )
        beer_garden.router.route(
            Operation(
                operation_type="COMMAND_BLOCK_LIST_REMOVE",
                args=[command_publishing_id],
                target_garden_name=blocked_command["namespace"],
            )
        )

        self.set_status(204)


class CommandPublishingBlockListAPI(AuthorizationHandler):
    def get(self):
        """
        ---
        summary: Retrieve list of commands in publishing block list
        responses:
          201:
            description: list of commands in publishing block list
            schema:
              $ref: '#/definitions/CommandPublishingBlocklist'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Command Block List
        """
        response = beer_garden.router.route(
            Operation(
                operation_type="COMMAND_BLOCK_LIST_GET",
            )
        )

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
              type: array
              items:
                  $ref: '#/definitions/CommandPublishingBlocklist'
        consumes:
          - application/json
        responses:
          201:
            description: Command has been added to publishing block list
            schema:
              $ref: '#/definitions/CommandPublishingBlocklist'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Command Block List
        """
        errors = []
        for command in self.request_body:
            systems = System.objects(namespace=command["namespace"], name=command["system"])
            try:
                self.get_or_raise(System, SYSTEM_UPDATE, id=systems[0].id)
                if config.get("garden.name") != command["namespace"]:
                    blocked_command = beer_garden.router.route(
                        Operation(
                            operation_type="COMMAND_BLOCK_LIST_ADD",
                            kwargs={"command": command},
                            target_garden_name=config.get("garden.name"),
                        )
                    )
                    command["id"] = blocked_command._data["id"].__str__()

                beer_garden.router.route(
                    Operation(
                        operation_type="COMMAND_BLOCK_LIST_ADD",
                        kwargs={"command": command},
                        target_garden_name=command["namespace"],
                    )
                )
            except Exception as e:
                errors.append(f"{e.__str__()} for {command.__str__()}")

        self.set_status(201)
