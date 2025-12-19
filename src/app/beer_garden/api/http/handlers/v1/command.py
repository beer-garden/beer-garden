# -*- coding: utf-8 -*-
from brewtils.models import Operation, System

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.errors import EndpointRemovedException


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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Command'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Commands
        """

        _ = self.get_or_raise(System, id=system_id)

        response = await self.process_operation(
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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Command'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Command'
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Deprecated
        """

        permitted_objects_filter = self.permissioned_queryset(System)

        response = await self.process_operation(
            Operation(
                operation_type="COMMAND_READ_ALL",
                kwargs={
                    "q_filter": permitted_objects_filter,
                },
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
