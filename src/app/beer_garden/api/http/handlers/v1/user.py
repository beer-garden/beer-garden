# -*- coding: utf-8 -*-
import json

from mongoengine.errors import DoesNotExist, ValidationError
from passlib.apps import custom_app_context

import beer_garden.api.http

# from beer_garden.db.mongo.models import Principal, Role
# from beer_garden.db.mongo.parser import MongoParser
# from beer_garden.api.http.authorization import (
#     authenticated,
#     check_permission,
#     Permissions,
#     coalesce_permissions,
# )
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.errors import ModelValidationError, RequestForbidden
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser


class UserAPI(BaseHandler):
    async def get(self, user_identifier):
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
            response = SchemaParser.serialize(beer_garden.api.http.anonymous_principal)
        else:

            try:
                response = await self.client(
                    Operation(
                        operation_type="USER_READ",
                        kwargs={"user_id": str(user_identifier)},
                    )
                )
            except (DoesNotExist, ValidationError):
                response = await self.client(
                    Operation(
                        operation_type="USER_READ",
                        kwargs={"username": str(user_identifier)},
                    )
                )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self, user_id):
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

        await self.client(
            Operation(
                operation_type="USER_DELETE",
                kwargs={
                    "user_id": user_id,
                },
            )
        )

        self.set_status(204)

    async def patch(self, user_id):
        """
        ---
        summary: Partially update a User
        description: |
          The body of the request needs to contain a set of instructions
          detailing the updates to apply:
          ```JSON
          [
            { "operation": "add", "path": "/roles", "value": "admin" }
          ]
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

        # Most things only need a permission check if updating a different user
        if user_id != str(self.current_user.id):
            local_admin = False
            for permission in self.current_user.permissions:
                if permission.is_local and permission.access == "ADMIN":
                    local_admin = True
                    break
            if not local_admin:
                raise RequestForbidden("Invalid password")

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        response = {}

        for op in patch:
            if op.path == "/roles":

                try:
                    if op.operation == "add":
                        response = await self.client(
                            Operation(
                                operation_type="USER_UPDATE_ROLE",
                                kwargs={
                                    "user_id": user_id,
                                    "role_id": op.value,
                                },
                            )
                        )

                    elif op.operation == "remove":
                        response = await self.client(
                            Operation(
                                operation_type="USER_REMOVE_ROLE",
                                kwargs={
                                    "user_id": user_id,
                                    "role_id": op.value,
                                },
                            )
                        )
                    else:
                        raise ModelValidationError(
                            "Unsupported operation '%s'" % op.operation
                        )
                except DoesNotExist:
                    raise ModelValidationError("Role '%s' does not exist" % op.value)

            elif op.path == "/username":

                if op.operation == "update":
                    response = await self.client(
                        Operation(
                            operation_type="USER_UPDATE",
                            kwargs={
                                "user_id": user_id,
                                "updates": {"username": op.value},
                            },
                        )
                    )
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

                hash = custom_app_context.hash(new_password)

                response = await self.client(
                    Operation(
                        operation_type="USER_UPDATE",
                        kwargs={
                            "user_id": user_id,
                            "updates": {"hash": hash},
                        },
                    ),
                )

            elif op.path == "/preferences/theme":
                if op.operation == "set":
                    response = await self.client(
                        Operation(
                            operation_type="USER_UPDATE",
                            kwargs={
                                "user_id": user_id,
                                "updates": {"preferences": {"theme": op.value}},
                            },
                        ),
                    )
                else:
                    raise ModelValidationError(
                        "Unsupported operation '%s'" % op.operation
                    )

            else:
                raise ModelValidationError("Unsupported path '%s'" % op.path)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class UsersAPI(BaseHandler):
    async def get(self):
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

        principals = await self.client(Operation(operation_type="USER_READ_ALL"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(principals)

    async def post(self):
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

        response = await self.client(
            Operation(
                operation_type="USER_CREATE",
                kwargs={
                    "username": parsed["username"],
                    "roles": parsed["roles"],
                    "password_hash": custom_app_context.hash(parsed["password"]),
                },
            ),
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_status(201)
        self.write(response)
