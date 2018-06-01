import json
import logging

from passlib.apps import custom_app_context
from mongoengine.errors import DoesNotExist

from bg_utils.models import Principal, Role
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError


class UserAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    def get(self, user_id):
        """
        ---
        summary: Retrieve a specific User
        parameters:
          - name: user_id
            in: path
            required: true
            description: The ID of the User
            type: string
        responses:
          200:
            description: User with the given ID
            schema:
              $ref: '#/definitions/User'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        principal = Principal.objects.get(id=str(user_id))

        self.write(BeerGardenSchemaParser.serialize_principal(principal))

    def patch(self, user_id):
        """
        ---
        summary: Partially update a User
        description: |
          The body of the request needs to contain a set of instructions detailing the updates to
          apply:
          ```JSON
          {
            "operations": [
              { "operation": "add", "path": "/role", "value": "admin" }
            ]
          }
          ```
        parameters:
          - name: user_id
            in: path
            required: true
            description: The ID of the User
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the User
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: User with the given ID
            schema:
              $ref: '#/definitions/User'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        principal = Principal.objects.get(id=str(user_id))
        operations = BeerGardenSchemaParser.parse_patch(self.request.decoded_body,
                                                        many=True, from_string=True)

        for op in operations:
            if op.path == '/role':
                try:
                    role = Role.objects.get(name=op.value)
                except DoesNotExist:
                    error_msg = "Role '%s' does not exist" % op.value
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)

                if op.operation == 'add':
                    principal.roles.append(role)
                elif op.operation == 'remove':
                    principal.roles.remove(role)
                else:
                    error_msg = "Unsupported operation '%s'" % op.operation
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)
            else:
                error_msg = "Unsupported path '%s'" % op.path
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        principal.save()

        self.write(BeerGardenSchemaParser.serialize_principal(principal))


class UsersAPI(BaseHandler):

    def post(self):
        """
        ---
        summary: Create a new User
        parameters:
          - name: user
            in: body
            description: The User definition
            schema:
              $ref: '#/definitions/User'
        consumes:
          - application/json
        responses:
          201:
            description: A new User has been created
            schema:
              $ref: '#/definitions/User'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        parsed = json.loads(self.request.decoded_body)

        hash = custom_app_context.hash(parsed['password'])

        user = Principal(username=parsed['username'], hash=hash)
        user.save()
