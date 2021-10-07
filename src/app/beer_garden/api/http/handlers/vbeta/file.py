# -*- coding: utf-8 -*-
import io

from brewtils.models import Resolvable
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.db.mongo.models import RawFile


class RawFileAPI(BaseHandler):
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
        db_file = RawFile.objects.get(id=file_id)
        file = db_file.file.read()

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
            schema:
              $ref: '#/definitions/FileStatus'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        db_file = RawFile.objects.get(id=file_id)
        db_file.file.delete()
        db_file.save()

        self.set_status(204)


class RawFileListAPI(BaseHandler):
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
        db_file = RawFile()
        db_file.file.put(io.BytesIO(self.request.body))
        db_file.save()

        resolvable = Resolvable(id=str(db_file.id), type="bytes", storage="gridfs")
        response = SchemaParser.serialize(resolvable, to_string=True)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
