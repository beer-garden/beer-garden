# -*- coding: utf-8 -*-
from brewtils.models import Operation

from beer_garden.api.authorization import Permissions
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.db.mongo.api import MongoParser
from beer_garden.db.mongo.models import System
from beer_garden.errors import EndpointRemovedException

SYSTEM_CREATE = Permissions.SYSTEM_CREATE.value
SYSTEM_READ = Permissions.SYSTEM_READ.value
SYSTEM_UPDATE = Permissions.SYSTEM_UPDATE.value
SYSTEM_DELETE = Permissions.SYSTEM_DELETE.value


class CommandAPI(AuthorizationHandler):
    async def get(self, system_id, command_name):
        """
        ---
        summary: Retrieve a specific Command
        parameters:
          - name: system_id
            in: path
            required: true
            description: The ID of the System
            type: string
          - name: command_name
            in: path
            required: true
            description: The name of the Command
            type: string
        responses:
          200:
            description: Command with the given name
            schema:
              $ref: '#/definitions/Command'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Commands
        """
        _ = self.get_or_raise(System, SYSTEM_READ, id=system_id)

        response = await self.client(
            Operation(operation_type="COMMAND_READ", args=[system_id, command_name])
        )
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class CommandAPIOld(AuthorizationHandler):
    async def get(self, command_id):
        """
        ---
        summary: Retrieve a specific Command
        deprecated: true
        parameters:
          - name: command_id
            in: path
            required: true
            description: The ID of the Command
            type: string
        responses:
          200:
            description: Command with the given ID
            schema:
              $ref: '#/definitions/Command'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        raise EndpointRemovedException(
            message=(
                "This endpoint has been removed as Commands no longer have IDs. "
                "Please use /systems/<system_id>/commands/<command_name> instead."
            )
        )


class CommandListAPI(AuthorizationHandler):
    async def get(self):
        """
        ---
        summary: Retrieve all Commands
        deprecated: true
        responses:
          200:
            description: All Commands
            schema:
              type: array
              items:
                $ref: '#/definitions/Command'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        systems = self.permissioned_queryset(System, SYSTEM_READ)
        commands = []

        for system in systems:
            commands.extend(system.commands)

        response = MongoParser.serialize(commands, to_string=True)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
