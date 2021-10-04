# -*- coding: utf-8 -*-

from brewtils.errors import ModelValidationError
from brewtils.models import Operation, Resolvable
from brewtils.schema_parser import SchemaParser
from tornado.escape import json_decode

from beer_garden.api.http.base_handler import BaseHandler


class FileChunkAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Retrieve a File or FileChunk
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
          - name: chunk
            in: query
            required: false
            description: The chunk number requested
            type: integer
          - name: verify
            in: query
            required: false
            description: Flag that will cause verification information to
                         be returned instead of the file data
            type: boolean
        responses:
          200:
            description: The requested File or FileChunk data
            schema:
              $ref: '#/definitions/FileStatus'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_argument("file_id", default=None)
        chunk = self.get_argument("chunk", default=None)
        verify = self.get_argument("verify", default="").lower() == "true"

        if file_id is None:
            raise ValueError("Cannot fetch a file or chunk without a file ID.")

        response = await self.client(
            Operation(
                operation_type="FILE_FETCH",
                args=[file_id],
                kwargs={"chunk": chunk, "verify": verify},
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def post(self):
        """
        ---
        summary: Create a new FileChunk
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
          - name: upsert
            in: query
            required: false
            description: Creates a top-level file if one doesn't exist
            type: boolean
          - name: body
            in: body
            required: true
            description: Data - A Base64 string encoding your data;
                         Offset - The chunk number (0, 1, ... N)
            schema:
              properties:
                "data":
                  type: string
                  format: byte
                "offset":
                  type: integer
        responses:
          201:
            description: A new FileChunk is created
            schema:
              $ref: '#/definitions/FileStatus'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_argument("file_id", default=None)
        upsert = self.get_argument("upsert", default="").lower() == "true"

        args = json_decode(self.request.body)
        data = args.get("data", None)
        offset = args.get("offset", None)

        if file_id is None:
            raise ModelValidationError("No file id provided.")
        if data is None:
            raise ModelValidationError(f"No data sent to write to file {file_id}")
        if offset is None:
            raise ModelValidationError(
                f"No offset sent with data to write to file {file_id}"
            )

        response = await self.client(
            Operation(
                operation_type="FILE_CHUNK",
                args=[file_id, offset, data],
                kwargs={"upsert": upsert},
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self):
        """
        ---
        summary: Delete a file
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
        responses:
          200:
            description: The file and all of its contents have been removed.
            schema:
              $ref: '#/definitions/FileStatus'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_argument("file_id", default=None)
        if file_id is None:
            raise ValueError("Cannot delete a file without an id.")

        response = await self.client(
            Operation(operation_type="FILE_DELETE", args=[file_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class ChunkNameAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Reserve a file ID for a new file.
        parameters:
          - name: file_name
            in: query
            required: true
            description: The name of the file being sent.
          - name: chunk_size
            in: query
            required: true
            description: The size of chunks the file is being broken into (in bytes).
            type: integer
          - name: file_size
            in: query
            required: true
            description: The total size of the file (in bytes).
            type: integer
          - name: file_id
            in: query
            required: false
            description: Attempt to set the file's ID. Must be a 24-character hex string.
            type: string
          - name: upsert
            in: query
            required: false
            description: Update an already-existing File, otherwise make a new one.
            type: boolean
          - name: owner_id
            in: query
            required: false
            description: Used to set ownership of the file so it isn't deleted.
            type: string
          - name: owner_type
            in: query
            required: false
            description: Describes the type of owner.
                This may be any value, or a pre-set one (e.g. JOB, REQUEST, MyCustomOwnerType)
            type: string
        responses:
          200:
            description: The File ID
            schema:
              $ref: '#/definitions/FileStatus'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_name = self.get_argument("file_name", default="")
        file_size = self.get_argument("file_size", default=None)
        chunk_size = self.get_argument("chunk_size", default=None)
        file_id = self.get_argument("file_id", default=None)
        owner_id = self.get_argument("owner_id", default=None)
        owner_type = self.get_argument("owner_type", default=None)
        upsert = self.get_argument("upsert", default="").lower() == "true"

        if chunk_size is None:
            raise ModelValidationError(f"No chunk_size sent with file {file_name}.")
        if file_size is None:
            raise ModelValidationError(f"No file_size sent with file {file_name}.")

        file_status = await self.client(
            Operation(
                operation_type="FILE_CREATE",
                args=[file_name, int(file_size), int(chunk_size)],
                kwargs={
                    "file_id": file_id,
                    "upsert": upsert,
                    "owner_id": owner_id,
                    "owner_type": owner_type,
                },
            ),
            serialize_kwargs={"to_string": False},
        )

        resolvable = Resolvable(
            id=file_status["file_id"],
            type="chunk",
            storage="gridfs",
            details=file_status,
        )
        response = SchemaParser.serialize(resolvable, to_string=True)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
