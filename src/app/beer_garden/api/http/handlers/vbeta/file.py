# -*- coding: utf-8 -*-
import io
from urllib.parse import unquote

import tornado
from brewtils.models import Operation, Permissions, Resolvable
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.db.mongo.models import RawFile
from beer_garden.garden import local_garden
from beer_garden.metrics import collect_metrics


class RawFileAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="RawFileAPI")
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
            schema:
              $ref: '#/definitions/FileStatus'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """

        self.verify_user_permission_for_object(local_garden())
        db_file = RawFile.objects.get(id=file_id)
        file = db_file.file.read()

        self.set_header("Content-Type", "application/octet-stream")
        self.write(file)

    @collect_metrics(transaction_type="API", group="RawFileAPI")
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
            schema:
              $ref: '#/definitions/FileStatus'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        self.minimum_permission = Permissions.OPERATOR.name

        self.verify_user_permission_for_object(local_garden())
        db_file = RawFile.objects.get(id=file_id)
        db_file.file.delete()
        db_file.save()

        self.set_status(204)


MAX_CHUNK_SIZE = 1024 * 1024 * 15  # 15MB


# TODO: Implement JS to support this: https://www.npmjs.com/package/ng-file-upload
@tornado.web.stream_request_body
class FileStreamAPI(AuthorizationHandler):
    def initialize(self):
        self.chunk_data = []
        self.file_size = 0

    def prepare(self):
        self.request.connection.set_max_body_size(MAX_CHUNK_SIZE)

    def data_received(self, chunk):
        self.chunk_data.append(chunk)
        self.file_size += len(chunk)

    @collect_metrics(transaction_type="API", group="FileStreamAPI")
    async def put(self, filename):
        filename = unquote(filename)
        # file_name = self.get_argument("file_name", default="")
        file_id = self.get_argument("file_id", default=None)
        owner_id = self.get_argument("owner_id", default=None)
        owner_type = self.get_argument("owner_type", default=None)
        upsert = self.get_argument("upsert", default="").lower() == "true"
        md5_sum = self.get_argument("md5_sum", default=None)

        file = await self.process_operation(
            Operation(
                operation_type="FILE_CREATE",
                args=[filename, self.file_size, len(self.chunk_data)],
                kwargs={
                    "file_id": file_id,
                    "upsert": upsert,
                    "owner_id": owner_id,
                    "owner_type": owner_type,
                    "md5_sum": md5_sum,
                },
            ),
            serialize_kwargs={"to_string": False},
        )

        offset = 0
        for chunk in self.chunk_data:
            response = await self.process_operation(
                Operation(
                    operation_type="FILE_CHUNK",
                    args=[file["file_id"], offset, chunk],
                    kwargs={"upsert": upsert},
                )
            )
            offset += len(chunk)

        response = await self.process_operation(
            Operation(
                operation_type="FILE_FETCH",
                kwargs={
                    "file_id": file["file_id"],
                    "verify": True,
                },
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class RawFileListAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="RawFileListAPI")
    async def post(self):
        """
        ---
        summary: Create a new File
        parameters:
          - name: body
            in: body
            required: true
            description: The data
        responses:
          201:
            description: A new File is created
            schema:
              $ref: '#/definitions/FileStatus'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        self.minimum_permission = Permissions.OPERATOR.name

        self.verify_user_permission_for_object(local_garden())
        db_file = RawFile()
        db_file.file.put(io.BytesIO(self.request.body))
        db_file.save()

        resolvable = Resolvable(id=str(db_file.id), type="bytes", storage="gridfs")
        response = SchemaParser.serialize(resolvable, to_string=True)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
