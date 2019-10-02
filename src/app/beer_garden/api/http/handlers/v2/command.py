from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.api.http.client import ExecutorClient


class CommandAPI(BaseHandler):
    @authenticated(permissions=[Permissions.COMMAND_READ])
    async def get(self, namespace, command_id):
        """
        ---
        summary: Retrieve a specific Command
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ExecutorClient() as client:
            thrift_response = await client.getCommand(namespace, command_id)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)


class CommandListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.COMMAND_READ])
    async def get(self, namespace):
        """
        ---
        summary: Retrieve all Commands
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ExecutorClient() as client:
            thrift_response = await client.getCommands(namespace)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)
