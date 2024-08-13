# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Permissions
from brewtils.schema_parser import SchemaParser
from marshmallow import ValidationError

from beer_garden.api.http.exceptions import BadRequest
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.user import UserPasswordChangeSchema
from beer_garden.errors import InvalidPasswordException
from beer_garden.metrics import collect_metrics


class UserAPI(AuthorizationHandler):
    parser = SchemaParser()

    @collect_metrics(transaction_type="API", group="UserAPI")
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
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        response = await self.process_operation(
            Operation(
                operation_type="USER_READ",
                args=[username],
            )
        )

        self.write(response)

    @collect_metrics(transaction_type="API", group="UserAPI")
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

    @collect_metrics(transaction_type="API", group="UserAPI")
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

    @collect_metrics(transaction_type="API", group="UserListAPI")
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
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        response = await self.process_operation(
            Operation(
                operation_type="USER_READ_ALL",
            )
        )

        self.write(response)

    @collect_metrics(transaction_type="API", group="UserListAPI")
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
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()

        user_model = self.parser.parse_user(self.request.decoded_body, from_string=True)

        response = await self.process_operation(
            Operation(operation_type="USER_CREATE", args=[user_model]),
            filter_results=False,
        )

        self.write(response)
        self.set_status(201)

    @collect_metrics(transaction_type="API", group="UserListAPI")
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
        parameters:
          - name: patch
            in: body
            required: true
            description: |
              Instructions for how to update the User
            schema:
              $ref: '#/definitions/Patch'
        responses:
          204:
            description: Patch operation has been successfully forwarded
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
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

    @collect_metrics(transaction_type="API", group="UserPasswordChangeAPI")
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

    @collect_metrics(transaction_type="API", group="WhoAmIAPI")
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
