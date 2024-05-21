# -*- coding: utf-8 -*-
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden

from brewtils.models import Operation


class RoleAPI(AuthorizationHandler):

    async def delete(self, role):
        """
        ---
        summary: Delete a specific User
        parameters:
          - name: role
            in: path
            required: true
            description: The role name of the Role
            type: string
        responses:
          204:
            description: Role has been successfully deleted
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
                operation_type="ROLE_DELETE",
                kwargs={
                    "role_name": role,
                },
            )
        )

        self.set_status(204)

    async def patch(self, role):
        """
        ---
        summary: Partially update a User
        parameters:
          - name: role
            in: path
            required: true
            description: The role name of the Role
            type: string
          - name: patch
            in: body
            required: true
            description: |
              A subset of Role attributes to update
            schema:
              $ref: '#/definitions/UserPatch'
        responses:
          200:
            description: Role with the given role name
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

        patch = self.parser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "update_role":
                response = await self.process_operation(
                    Operation(
                        operation_type="ROLE_UPDATE",
                        kwargs={
                            "role_name": role,
                            "role": op.value,
                        },
                    )
                )

        self.write(response)


class RoleListAPI(AuthorizationHandler):
    async def get(self):
        """
        ---
        summary: Retrieve all Roles
        responses:
          200:
            description: All Roles
            schema:
              $ref: '#/definitions/RoleList'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        self.minimum_permission = self.GARDEN_ADMIN
        self.verify_user_permission_for_object(local_garden())

        response = await self.process_operation(
            Operation(operation_type="ROLE_READ_ALL")
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def post(self):
        """
        ---
        summary: Create a new Role
        parameters:
          - name: role
            in: body
            description: The role
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
          - Users
        """
        self.minimum_permission = self.GARDEN_ADMIN
        self.verify_user_global_permission()

        role_model = self.parser.parse_role(self.request.decoded_body, from_string=True)

        response = await self.process_operation(
            Operation(operation_type="ROLE_CREATE", args=[role_model])
        )

        self.write(response)
        self.set_status(201)
