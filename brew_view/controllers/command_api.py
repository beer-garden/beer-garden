import logging

from bg_utils.models import Command
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler


class CommandAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.COMMAND_READ])
    def get(self, command_id):
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
        self.logger.debug("Getting Command: %s", command_id)

        self.write(self.parser.serialize_command(Command.objects.get(id=str(command_id)),
                                                 to_string=False))
