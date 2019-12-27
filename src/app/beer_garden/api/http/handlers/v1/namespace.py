# -*- coding: utf-8 -*-
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class NamespaceAPI(BaseHandler):
    @authenticated(permissions=[Permissions.SYSTEM_READ])
    async def get(self, namespace):
        """
        ---
        summary: Delete a specific Instance
        parameters:
          - name: namespace
            in: path
            required: true
            description: Namespace to use
            type: string
        responses:
          200:
            description: Namespace with the given namespace
            schema:
              $ref: '#/definitions/Instance'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        response = await self.client.get_namespace(namespace)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.SYSTEM_DELETE])
    async def delete(self, namespace):
        """
        ---
        summary: Delete a specific Instance
        parameters:
          - name: namespace
            in: path
            required: true
            description: Namespace to use
            type: string
        responses:
          204:
            description: Instance has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        await self.client.remove_namespace(namespace)

        self.set_status(204)

    @authenticated(permissions=[Permissions.SYSTEM_UPDATE])
    async def patch(self, namespace):
        """
        ---
        summary: Partially update a Namespace
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * initializing
          * running
          * stopped
          * block

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        parameters:
          - name: namespace
            in: path
            required: true
            description: Namespace to use
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the System
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Namespace with the given namespace
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        response = await self.client.update_namespace(
            namespace,
            SchemaParser.parse_patch(self.request.decoded_body, from_string=True),
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.SYSTEM_CREATE])
    async def post(self, namespace):
        """
        ---
        summary: Create a new Namespace or update an existing Namespace
        description: |
            If the Namespace does not exist it will be created. If the Namespace
            already exists it will be updated (assuming it passes validation).
        parameters:
          - name: namespace
            in: path
            required: true
            description: Namespace to use
            type: string
          - name: namespace-body
            in: body
            description: The Namespace definition to create / update
            schema:
              $ref: '#/definitions/Namespace'
        responses:
          200:
            description: An existing System has been updated
            schema:
              $ref: '#/definitions/Namespace'
          201:
            description: A new System has been created
            schema:
              $ref: '#/definitions/Namespace'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        response = await self.client.create_namespace(
            SchemaParser.parse_namespace(self.request.decoded_body, from_string=True)
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
