# -*- coding: utf-8 -*-
import json

from brewtils.schema_parser import SchemaParser

import beer_garden.api.http
from beer_garden.api.auth import (
    Permissions,
    authenticated,
    check_permission,
    coalesce_permissions,
)
from beer_garden.api.http.base_handler import BaseHandler


class UserAPI(BaseHandler):
    async def get(self, user_id):
        """
        ---
        summary: Retrieve a specific User
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
          - name: user_id
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
        if user_id == "anonymous":
            principal = beer_garden.api.http.anonymous_principal
        else:
            # Need fine-grained access control here
            if user_id not in [str(self.current_user.id), self.current_user.username]:
                check_permission(self.current_user, [Permissions.USER_READ])

            principal = await self.client.get_user(
                self.request.namespace,
                user_id=user_id,
                serialize_kwargs={"serialize": False},
            )

            if principal is None:
                principal = await self.client.get_user(
                    self.request.namespace,
                    user_name=user_id,
                    serialize_kwargs={"serialize": False},
                )

        principal.permissions = coalesce_permissions(principal.roles)[1]

        self.write(SchemaParser.serialize_principal(principal, to_string=False))

    @authenticated(permissions=[Permissions.USER_DELETE])
    async def delete(self, user_id):
        """
        ---
        summary: Delete a specific User
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
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
        await self.client.remove_user(self.request.namespace, user_id)

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
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
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
        user = await self.client.update_user(
            self.request.namespace,
            user_id,
            SchemaParser.parse_patch(self.request.decoded_body, from_string=True),
            serialize_kwargs={"serialize": False},
        )

        user.permissions = coalesce_permissions(user.roles)[1]

        self.write(SchemaParser.serialize_principal(user, to_string=False))


class UsersAPI(BaseHandler):
    @authenticated(permissions=[Permissions.USER_READ])
    async def get(self):
        """
        ---
        summary: Retrieve all Users
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
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
        principals = await self.client.get_users(
            self.request.namespace, serialize_kwargs={"serialize": False}
        )

        for principal in principals:
            principal.permissions = coalesce_permissions(principal.roles)[1]

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            SchemaParser.serialize_principal(principals, to_string=True, many=True)
        )

    @authenticated(permissions=[Permissions.USER_CREATE])
    async def post(self):
        """
        ---
        summary: Create a new User
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
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

        user = await self.client.create_user(
            self.request.namespace,
            parsed["username"],
            parsed["password"],
            serialize_kwargs={"serialize": False},
        )

        user.permissions = coalesce_permissions(user.roles)[1]

        self.set_status(201)
        self.write(SchemaParser.serialize_principal(user, to_string=False))
