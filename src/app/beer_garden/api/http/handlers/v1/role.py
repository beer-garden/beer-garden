# -*- coding: utf-8 -*-
from mongoengine.errors import DoesNotExist

import beer_garden.api.http
from beer_garden.api.http.authorization import (
    anonymous_principal,
    authenticated,
    Permissions,
)
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser


class RoleAPI(BaseHandler):
    parser = SchemaParser()

    @authenticated(permissions=[Permissions.ADMIN])
    async def get(self, role_id):
        """
        ---
        summary: Retrieve all specific Role
        parameters:
          - name: role_id
            in: path
            required: true
            description: The ID of the Role
            type: string
        responses:
          200:
            description: Role with the given ID
            schema:
              $ref: '#/definitions/Role'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """

        role = await self.client(
            Operation(
                operation_type="ROLE_READ",
                kwargs={
                    "role_id": role_id
                },
            )
        )

        self.write(role)

    @authenticated(permissions=[Permissions.ADMIN])
    async def delete(self, role_id):
        """
        ---
        summary: Delete a specific Role
        parameters:
          - name: role_id
            in: path
            required: true
            description: The ID of the Role
            type: string
        responses:
          204:
            description: Role has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        await self.client(
            Operation(
                operation_type="ROLE_DELETE",
                kwargs={
                    "role_id": role_id,
                },
            )
        )

        self.set_status(204)

    @authenticated(permissions=[Permissions.ADMIN])
    async def patch(self, role_id):
        """
        ---
        summary: Partially update a Role
        description: |
          The body of the request needs to contain a set of instructions
          detailing the updates to apply:
          ```JSON
          [
            { "operation": "add", "path": "/permissions", "value": "ALL" }
          ]
          ```
        parameters:
          - name: role_id
            in: path
            required: true
            description: The ID of the Role
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Role
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Role with the given ID
            schema:
              $ref: '#/definitions/Role'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            if op.path == "/permissions":
                try:
                    if op.operation == "add":
                        role = await self.client(
                            Operation(
                                operation_type="ROLE_UPDATE_PERMISSION",
                                kwargs={
                                    "role_id": role_id,
                                    "permission": self.parser.parse_permission(
                                        op.value, from_string=False
                                    ),
                                },
                            )
                        )
                    elif op.operation == "remove":
                        role = await self.client(
                            Operation(
                                operation_type="ROLE_REMOVE_PERMISSION",
                                kwargs={
                                    "role_id": role_id,
                                    "permission": self.parser.parse_permission(
                                        op.value, from_string=False
                                    ),
                                },
                            )
                        )
                    else:
                        raise ModelValidationError(
                            "Unsupported operation '%s'" % op.operation
                        )
                except ValueError:
                    raise ModelValidationError(
                        "Permission '%s' does not exist" % op.value
                    )

                except DoesNotExist:
                    raise ModelValidationError("Role '%s' does not exist" % op.value)

            elif op.path == "/description":
                if op.operation != "update":
                    raise ModelValidationError(
                        "Unsupported operation '%s'" % op.operation
                    )

                role = await self.client(
                    Operation(
                        operation_type="ROLE_UPDATE_DESCRIPTION",
                        kwargs={
                            "role_id": role_id,
                            "description": op.value
                        },
                    )
                )

            else:
                raise ModelValidationError("Unsupported path '%s'" % op.path)

        # Any modification to roles will possibly modify the anonymous user
        beer_garden.api.http.anonymous_principal = anonymous_principal()

        self.write(role)


class RolesAPI(BaseHandler):
    parser = SchemaParser()

    @authenticated(permissions=[Permissions.ADMIN])
    async def get(self):
        """
        ---
        summary: Retrieve all Roles
        responses:
          200:
            description: All Roles
            schema:
              type: array
              items:
                $ref: '#/definitions/Role'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        response = await self.client(Operation(operation_type="ROLE_READ_ALL"))
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.ADMIN])
    async def post(self):
        """
        ---
        summary: Create a new Role
        parameters:
          - name: role
            in: body
            description: The Role definition
            schema:
              $ref: '#/definitions/Role'
        consumes:
          - application/json
        responses:
          201:
            description: A new Role has been created
            schema:
              $ref: '#/definitions/Role'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """

        role = self.parser.parse_role(
            self.request.decoded_body, from_string=True
        )

        response = await self.client(
            Operation(
                operation_type="ROLE_CREATE",
                args=[role],
            )
        )

        self.set_status(201)
        self.write(response)

