from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.errors import EndpointRemovedException


class CommandPublishingBlocklistPathAPI(AuthorizationHandler):
    def delete(self, command_publishing_id):
        """
        ---
        summary: Remove a command from event publishing block list
        deprecated: true
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
          - Deprecated
        """
        raise EndpointRemovedException(
            message=("Command publishing blocklist API has been removed.")
        )


class CommandPublishingBlocklistAPI(AuthorizationHandler):
    def get(self):
        """
        ---
        summary: Retrieve list of commands in publishing block list
        deprecated: true
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
          - Deprecated
        """
        raise EndpointRemovedException(
            message=("Command publishing blocklist API has been removed.")
        )

    def post(self):
        """
        ---
        summary: Add a list of commands to event publishing block list
        deprecated: true
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
          - Deprecated
        """
        raise EndpointRemovedException(
            message=("Command publishing blocklist API has been removed.")
        )
