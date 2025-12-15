# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions
from brewtils.schema_parser import SchemaParser
from marshmallow import ValidationError

from beer_garden.api.http.exceptions import BadRequest
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.user import UserPasswordChangeSchema
from beer_garden.errors import InvalidPasswordException


class UserAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self, username):
        """
        ---
        summary: Retrieve a specific User
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
        responses:
          200:
            description: User with the given username
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/User'
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
          - Users
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        response = await self.process_operation(
            Operation(
                operation_type="USER_READ",
                args=[username],
            )
        )

        self.write(response)

    async def delete(self, username):
        """
        ---
        summary: Delete a specific User
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
        responses:
          204:
            description: User has been successfully deleted
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
          - Users
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()
        await self.process_operation(
            Operation(
                operation_type="USER_DELETE",
                args=[username],
            ),
            filter_results=False,
        )

        self.set_status(204)

    async def patch(self, username):
        """
        ---
        summary: Partially update a User
        requestBody:
          name: patch
          description: |
              A subset of User attributes to update, most commonly the password.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
        responses:
          200:
            description: User with the given username
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/User'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
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
          - Users
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "update_roles":
                response = await self.process_operation(
                    Operation(
                        operation_type="USER_UPDATE",
                        kwargs={
                            "username": username,
                            "roles": op.value["roles"],
                        },
                    ),
                    filter_results=False,
                )
            elif operation == "update_user_mappings":
                response = await self.process_operation(
                    Operation(
                        operation_type="USER_UPDATE",
                        kwargs={
                            "username": username,
                            "remote_user_mapping": SchemaParser.parse_alias_user_map(
                                op.value["user_alias_mapping"],
                                from_string=False,
                                many=True,
                            ),
                        },
                    ),
                    filter_results=False,
                )
            elif operation == "update_user_password":
                response = await self.process_operation(
                    Operation(
                        operation_type="USER_UPDATE",
                        kwargs={
                            "username": username,
                            "new_password": op.value["password"],
                        },
                    ),
                    filter_results=False,
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")
        if response:
            self.write(response)
        else:
            raise ModelValidationError(f"Missing Operations '{patch}'")


class UserListAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self):
        """
        ---
        summary: Retrieve all Users
        responses:
          200:
            description: All Users
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/UserList'
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Users
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        response = await self.process_operation(
            Operation(
                operation_type="USER_READ_ALL",
            )
        )

        self.write(response)

    async def post(self):
        """
        ---
        summary: Create a new User
        requestBody:
          name: patch
          description: The user
          content:
              application/json:
                schema:
                  $ref: '#/components/schemas/User'
        consumes:
          - application/json
        responses:
          201:
            description: A new User has been created
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/User'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Users
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()

        user_model = self.parser.parse_user(self.request.decoded_body, from_string=True)

        response = await self.process_operation(
            Operation(operation_type="USER_CREATE", args=[user_model]),
            filter_results=False,
        )

        self.write(response)
        self.set_status(201)

    async def patch(self):
        """
        ---
        summary: Partially update a User
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * rescan

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        requestBody:
          name: patch
          description: Instructions for how to update the User
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        responses:
          204:
            description: Patch operation has been successfully forwarded
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
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
          - Users
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "rescan":
                await self.process_operation(
                    Operation(operation_type="USER_RESCAN"), filter_results=False
                )

        self.set_status(204)


class UserPasswordChangeAPI(AuthorizationHandler):

    async def post(self):
        """
        ---
        summary: Allows a user to change their own password
        requestBody:
          name: password_change
          description: The current password for verification and the new password
          content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserPasswordChange'
        consumes:
          - application/json
        responses:
          204:
            description: The password has been changed
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Password
        """
        user = self.current_user

        try:
            password_data = UserPasswordChangeSchema().load(self.request_body)
        except ValidationError as exc:
            raise BadRequest(reason=f"{exc}")

        try:
            await self.process_operation(
                Operation(
                    operation_type="USER_UPDATE",
                    kwargs={
                        "user": user,
                        "current_password": password_data["current_password"],
                        "new_password": password_data["new_password"],
                    },
                )
            )
        except InvalidPasswordException as exc:
            raise BadRequest(reason=f"{exc}")

        self.set_status(204)


class WhoAmIAPI(AuthorizationHandler):

    def get(self):
        """
        ---
        summary: Retrieve requesting User
        responses:
          200:
            description: Requesting User
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/User'
          401:
            $ref: '#/components/schemas/401Error'
          403:
            $ref: '#/components/schemas/403Error'
        tags:
          - Users
        """

        response = SchemaParser.serialize_user(self.current_user, to_string=False)

        self.write(response)
