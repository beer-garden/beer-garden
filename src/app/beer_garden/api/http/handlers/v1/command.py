# -*- coding: utf-8 -*-
from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.models import Forward


class CommandAPI(BaseHandler):
    @authenticated(permissions=[Permissions.COMMAND_READ])
    async def get(self, command_id):
        """
        ---
        summary: Retrieve a specific Command
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
          - Commands
        """

        response = await self.client(
            Forward(forward_type="COMMAND_READ", args=[command_id])
        )
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class CommandListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.COMMAND_READ])
    async def get(self):
        """
        ---
        summary: Retrieve all Commands
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
          - Commands
        """

        response = await self.client(Forward(forward_type="COMMAND_READ_ALL"))
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
