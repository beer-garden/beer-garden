# -*- coding: utf-8 -*-
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class GardenAPI(BaseHandler):
    @authenticated(permissions=[Permissions.SYSTEM_READ])
    async def get(self, garden_name):
        """
        ---
        summary: Retrieve a specific Garden
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
        responses:
          200:
            description: Garden with the given garden_name
            schema:
              $ref: '#/definitions/Instance'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        response = await self.client.get_garden(garden_name)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.SYSTEM_DELETE])
    async def delete(self, garden_name):
        """
        ---
        summary: Delete a specific Garden
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
        responses:
          204:
            description: Garden has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        await self.client.remove_garden(garden_name)

        self.set_status(204)

    @authenticated(permissions=[Permissions.SYSTEM_UPDATE])
    async def patch(self, garden_name):
        """
        ---
        summary: Partially update a Garden
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
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Garden
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Garden with the given garden_name
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
            garden_name,
            SchemaParser.parse_patch(self.request.decoded_body, from_string=True),
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.SYSTEM_CREATE])
    async def post(self, garden_name):
        """
        ---
        summary: Create a new Garden or update an existing Garden
        description: |
            If the Garden does not exist it will be created. If the Garden
            already exists it will be updated (assuming it passes validation).
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
          - name: namespace-body
            in: body
            description: The Garden definition to create / update
            schema:
              $ref: '#/definitions/Namespace'
        responses:
          200:
            description: An existing Garden has been updated
            schema:
              $ref: '#/definitions/Namespace'
          201:
            description: A new Garden has been created
            schema:
              $ref: '#/definitions/Namespace'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """
        response = await self.client.create_garden(
            SchemaParser.parse_garden(self.request.decoded_body, from_string=True)
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
