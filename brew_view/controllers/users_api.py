import json
import logging

from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context

from bg_utils.models import Principal, Role
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.authorization import Permissions
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
        self.write(BeerGardenSchemaParser.serialize_principal(
            Principal.objects.get(id=str(user_id)),
            to_string=False
        ))

    def delete(self, user_id):
        """
        ---
        summary: Delete a specific User
        parameters:
          - name: user_id
            in: path
            required: true
            description: The ID of the User
            type: string
        responses:
          204:
            description: User has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        principal = Principal.objects.get(id=str(user_id))
        principal.delete()

        self.set_status(204)

    def patch(self, user_id):
        """
        ---
        summary: Partially update a User
        description: |
          The body of the request needs to contain a set of instructions
          detailing the updates to apply:
          ```JSON
          {
            "operations": [
              { "operation": "add", "path": "/roles", "value": "admin" }
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
        operations = BeerGardenSchemaParser.parse_patch(
            self.request.decoded_body,
            many=True,
            from_string=True
        )

        for op in operations:
            if op.path == '/roles':
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

            elif op.path == '/permissions':
                if op.value.upper() not in Permissions.__members__:
                    error_msg = "Permission '%s' does not exist" % op.value
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)

                if op.operation == 'add':
                    principal.permissions.append(op.value.upper())
                elif op.operation == 'remove':
                    principal.permissions.remove(op.value.upper())
                else:
                    error_msg = "Unsupported operation '%s'" % op.operation
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)

            else:
                error_msg = "Unsupported path '%s'" % op.path
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        principal.save()

        self.write(BeerGardenSchemaParser.serialize_principal(principal,
                                                              to_string=False))


class UsersAPI(BaseHandler):

    def get(self):
        """
        ---
        summary: Retrieve all Users
        responses:
          200:
            description: All Users
            schema:
              type: array
              items:
                $ref: '#/definitions/User'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        principals = Principal.objects.all().select_related(max_depth=1)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(BeerGardenSchemaParser.serialize_principal(
            principals,
            to_string=True,
            many=True
        ))

    def post(self):
        """
        ---
        summary: Create a new User
        parameters:
          - name: user
            in: body
            description: The user
            schema:
              type: object
              properties:
                username:
                  type: string
                  description: the name
                password:
                  type: string
                  description: the password
              required:
                - username
                - password
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

        user = Principal(username=parsed['username'],
                         hash=custom_app_context.hash(parsed['password']))
        user.save()

        self.set_status(204)
