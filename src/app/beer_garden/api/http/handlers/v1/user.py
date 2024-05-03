# -*- coding: utf-8 -*-
from brewtils.schema_parser import SchemaParser
from brewtils.models import Operation
from marshmallow import ValidationError

from beer_garden.api.http.exceptions import BadRequest
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.user import (
    UserPasswordChangeSchema,
)
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
            schema:
              $ref: '#/definitions/User'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        self.minimum_permission = self.GARDEN_ADMIN
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
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        self.minimum_permission = self.GARDEN_ADMIN
        self.verify_user_global_permission()
        await self.process_operation(
            Operation(
                operation_type="USER_DELETE",
                args=[username],
            )
        )

        self.set_status(204)

    async def patch(self, username):
        """
        ---
        summary: Partially update a User
        parameters:
          - name: username
            in: path
            required: true
            description: The username of the User
            type: string
          - name: patch
            in: body
            required: true
            description: |
              A subset of User attributes to update, most commonly the password.
            schema:
              $ref: '#/definitions/UserPatch'
        responses:
          200:
            description: User with the given username
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
        self.minimum_permission = self.GARDEN_ADMIN
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
                            "local_roles": [],
                        },
                    )
                )
            elif operation == "update_user_mappings":
                response = await self.process_operation(
                    Operation(
                        operation_type="USER_UPDATE",
                        kwargs={
                            "username": username,
                            "remote_user_mapping": SchemaParser.parse_remote_user_map(op.value["remote_user_mapping"], from_string=False, many=True),
                        },
                    )
                )
        
        self.write(response)


class UserListAPI(AuthorizationHandler):
    parser = SchemaParser()

    async def get(self):
        """
        ---
        summary: Retrieve all Users
        responses:
          200:
            description: All Users
            schema:
              $ref: '#/definitions/UserList'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Users
        """
        self.minimum_permission = self.GARDEN_ADMIN
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
        parameters:
          - name: user
            in: body
            description: The user
            schema:
              $ref: '#/definitions/UserCreate'
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
        self.minimum_permission = self.GARDEN_ADMIN
        self.verify_user_global_permission()

        user_model = self.parser.parse_user(self.request.decoded_body, from_string=True)

        response = await self.process_operation(
            Operation(operation_type="USER_CREATE", args=[user_model])
        )

        self.write(response)
        self.set_status(201)


class UserPasswordChangeAPI(AuthorizationHandler):
    async def post(self):
        """
        ---
        summary: Allows a user to change their own password
        parameters:
          - name: password_change
            in: body
            description: The current password for verification and the new password
            schema:
              $ref: '#/definitions/UserPasswordChange'
        consumes:
          - application/json
        responses:
          204:
            description: The password has been changed
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Password
        """
        user = self.current_user

        try:
            password_data = (
                UserPasswordChangeSchema(strict=True).load(self.request_body).data
            )
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
            schema:
              $ref: '#/definitions/User'
          401:
            $ref: '#/definitions/401Error'
          403:
            $ref: '#/definitions/403Error'
        tags:
          - Users
        """

        response = SchemaParser.serialize_user(self.current_user, to_string=False)

        self.write(response)
