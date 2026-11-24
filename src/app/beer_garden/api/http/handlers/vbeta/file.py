# -*- coding: utf-8 -*-
import io

from brewtils.models import Operation, Permissions

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden


class RawFileAPI(AuthorizationHandler):

    async def get(self, file_id):
        """
        ---
        summary: Retrieve a File
        parameters:
          - name: file_id
            in: path
            required: true
            description: The file ID
            type: string
        responses:
          200:
            description: The requested File or FileChunk data
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/FileStatus'
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
          - Files
        """

        self.verify_user_permission_for_object(local_garden())

        file = await self.process_operation(
            Operation(
                operation_type="RAW_FILE_READ",
                args=[file_id],
            ),
            serialize_kwargs={"return_raw": True},
        )

        self.set_header("Content-Type", "application/octet-stream")
        self.write(file)

    async def delete(self, file_id):
        """
        ---
        summary: Delete a file
        parameters:
          - name: file_name
            in: path
            required: true
            description: The file ID
            type: string
        responses:
          204:
            description: The file and all of its contents have been removed.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/FileStatus'
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
          - Files
        """
        self.minimum_permission = Permissions.OPERATOR.name

        self.verify_user_permission_for_object(local_garden())

        await self.process_operation(
            Operation(
                operation_type="RAW_FILE_DELETE",
                args=[file_id],
            ),
        )

        self.set_status(204)


class RawFileListAPI(AuthorizationHandler):

    async def post(self):
        """
        ---
        summary: Create a new File
        requestBody:
          name: body
          description: The data
          content:
            application/json:
              schema:
                type: string
                format: binary
        responses:
          201:
            description: A new File is created
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/FileStatus'
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
          - Files
        """
        self.minimum_permission = Permissions.OPERATOR.name

        self.verify_user_permission_for_object(local_garden())

        response = await self.process_operation(
            Operation(
                operation_type="RAW_FILE_CREATE",
                args=[io.BytesIO(self.request.body)],
            ),
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
