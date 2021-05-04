# -*- coding: utf-8 -*-
import io

from brewtils.resolvers.bytes import BYTES_PREFIX

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.db.mongo.models import RawFile


class RawFileAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve a File
        parameters:
          - name: file_id
            in: query
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
        db_file = RawFile.objects.get(id=self.get_argument("file_id", default=""))
        file = db_file.file.read()

        self.set_header("Content-Type", "application/octet-stream")
        self.write(file)

    @authenticated(permissions=[Permissions.CREATE])
    async def put(self):
        """
        ---
        summary: Create a new File
        parameters:
          - name: name
            in: query
            required: true
            description: The file name
            type: string
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
        name = self.get_argument("name", default="")
        db_file = RawFile(name=self.get_argument("name", default=""))
        db_file.file.put(io.BytesIO(self.request.body), filename=name)
        db_file.save()

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(BYTES_PREFIX + str(db_file.id))

    async def delete(self):
        """
        ---
        summary: Delete a file
        parameters:
          - name: file_name
            in: query
            required: true
            description: The name of the file
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
        db_file = RawFile.objects.get(name=self.get_argument("name", default=""))
        db_file.file.delete()
        db_file.save()

        self.set_status(204)
