import json
import logging

from mongoengine.errors import DoesNotExist, ValidationError
from passlib.apps import custom_app_context

import brew_view
from bg_utils.mongo.models import Principal, Role
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import (
    authenticated,
    check_permission,
    Permissions,
    coalesce_permissions,
)
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError, RequestForbidden


class UserAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    def get(self, user_identifier):
        """
        ---
        summary: Retrieve a specific User
        parameters:
          - name: user_identifier
            in: path
            required: true
            description: The ID or name of the User
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
        if user_identifier == "anonymous":
            principal = brew_view.anonymous_principal
        else:
            # Need fine-grained access control here
            if user_identifier not in [
                str(self.current_user.id),
                self.current_user.username,
            ]:
                check_permission(self.current_user, [Permissions.USER_READ])

            try:
                principal = Principal.objects.get(id=str(user_identifier))
            except (DoesNotExist, ValidationError):
                principal = Principal.objects.get(username=str(user_identifier))

        principal.permissions = coalesce_permissions(principal.roles)[1]

        self.write(MongoParser.serialize_principal(principal, to_string=False))

    @authenticated(permissions=[Permissions.USER_DELETE])
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
        operations = MongoParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        # Most things only need a permission check if updating a different user
        if user_id != str(self.current_user.id):
            check_permission(self.current_user, [Permissions.USER_UPDATE])

        for op in operations:
            if op.path == "/roles":
                # Updating roles always requires USER_UPDATE
                check_permission(self.current_user, [Permissions.USER_UPDATE])

                try:
                    if op.operation == "add":
                        principal.roles.append(Role.objects.get(name=op.value))
                    elif op.operation == "remove":
                        principal.roles.remove(Role.objects.get(name=op.value))
                    elif op.operation == "set":
                        principal.roles = [
                            Role.objects.get(name=name) for name in op.value
                        ]
                    else:
                        raise ModelValidationError(
                            "Unsupported operation '%s'" % op.operation
                        )
                except DoesNotExist:
                    raise ModelValidationError("Role '%s' does not exist" % op.value)

            elif op.path == "/username":

                if op.operation == "update":
                    principal.username = op.value
                else:
                    raise ModelValidationError(
                        "Unsupported operation '%s'" % op.operation
                    )

            elif op.path == "/password":
                if op.operation != "update":
                    raise ModelValidationError(
                        "Unsupported operation '%s'" % op.operation
                    )

                if isinstance(op.value, dict):
                    current_password = op.value.get("current_password")
                    new_password = op.value.get("new_password")
                else:
                    current_password = None
                    new_password = op.value

                if user_id == str(self.current_user.id):
                    if current_password is None:
                        raise ModelValidationError(
                            "In order to update your own password, you must provide "
                            "your current password"
                        )

                    if not custom_app_context.verify(
                        current_password, self.current_user.hash
                    ):
                        raise RequestForbidden("Invalid password")

                principal.hash = custom_app_context.hash(new_password)
                if "changed" in principal.metadata:
                    principal.metadata["changed"] = True

            elif op.path == "/preferences/theme":
                if op.operation == "set":
                    principal.preferences["theme"] = op.value
                else:
                    raise ModelValidationError(
                        "Unsupported operation '%s'" % op.operation
                    )

            else:
                raise ModelValidationError("Unsupported path '%s'" % op.path)

        principal.save()

        principal.permissions = coalesce_permissions(principal.roles)[1]
        self.write(MongoParser.serialize_principal(principal, to_string=False))


class UsersAPI(BaseHandler):
    @authenticated(permissions=[Permissions.USER_READ])
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

        for principal in principals:
            principal.permissions = coalesce_permissions(principal.roles)[1]

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            MongoParser.serialize_principal(principals, to_string=True, many=True)
        )

    @authenticated(permissions=[Permissions.USER_CREATE])
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

        user = Principal(
            username=parsed["username"],
            hash=custom_app_context.hash(parsed["password"]),
        )

        if "roles" in parsed:
            user.roles = [Role.objects.get(name=name) for name in parsed["roles"]]

        user.save()
        user.permissions = coalesce_permissions(user.roles)[1]

        self.set_status(201)
        self.write(MongoParser.serialize_principal(user, to_string=False))
