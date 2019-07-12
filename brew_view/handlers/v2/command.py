import logging

import mongoengine.errors

from bg_utils.mongo.models import Command
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler


class CommandAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.COMMAND_READ])
    def get(self, namespace, command_id):
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
        self.write(
            self.parser.serialize_command(
                Command.objects.get(id=str(command_id), namespace=namespace),
                to_string=False
            )
        )


class CommandListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.COMMAND_READ])
    def get(self, namespace):
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
        self.logger.debug("Getting Commands")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        try:
            self.write(
                self.parser.serialize_command(
                    Command.objects(namespace=namespace), many=True, to_string=True
                )
            )
        except mongoengine.errors.DoesNotExist as ex:
            self.logger.error(
                "Got an error while attempting to serialize commands. "
                "This error usually indicates "
                "there are orphans in the database."
            )
            raise mongoengine.errors.InvalidDocumentError(ex)
