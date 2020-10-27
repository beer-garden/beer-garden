# -*- coding: utf-8 -*-
import os
from base64 import b64decode

import tornado.web

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler, event_wait
import beer_garden.db.api as db
from brewtils.errors import ModelValidationError
from brewtils.models import File, FileChunk

BASEDIR_NAME = os.path.dirname(__file__)
BASEDIR_PATH = os.path.abspath(BASEDIR_NAME)
FILES_ROOT = os.path.join(BASEDIR_PATH, 'files')

MAX_STREAM_SIZE = 1024 * 1024 * 1024

print(f"~~~~~~~~~~~~~~~~~~~~~~~~~FILE ROOT PATH: {FILES_ROOT}")


class FileAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve a specific file
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
        responses:
          200:
            description: File with the given ID
            schema:
              $ref: '#/definitions/Request'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_query_argument("file_id", default=None)
        if file_id is None:
            raise ValueError("Cannot fetch a file without a file ID.")
        self.write(self._fetch_file(file_id))

    def _fetch_file(self, file_id):
        res = db.query_unique(File, id=file_id)
        if res is None:
            raise ModelValidationError("Tried to fetch an unsaved file.")
        # This is going to get big, try our best to be efficient
        all_data = [db.query_unique(FileChunk, file_id=res.id, n=x).data
                    for x in range(db.count(FileChunk, file_id=res.id))]
        return "".join(all_data)

    def _save_chunk(self, file_id, n, chunk_size, data):
        file = db.query_unique(File, id=file_id)
        if file is None:
            raise ValueError(f"Chunk cannot be saved, file with id {file_id} cannot be found")
        chunk = FileChunk(file_id=file.id, n=n, chunk_size=chunk_size, data=data)
        return db.create(chunk)

    @authenticated(permissions=[Permissions.CREATE])
    async def post(self):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
          - name: data
            in: body
            description: The Request definition
          - name: offset
            in: body
            description: The current offset definition
          - name: chunk_size
            in: body
            description: The size of chunks for the file
        responses:
          201:
            description: A new Request has been created
            schema:
              $ref: '#/definitions/Request'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Requests
        """
        file_id = self.get_query_argument("file_id", default=None)

        args = tornado.escape.json_decode(self.request.body)
        data = args.get('data', None)
        offset = args.get('offset', None)
        chunk_size = args.get('chunk_size', None)

        if data is None:
            raise ModelValidationError(f"No data sent to write to file {file_id}")
        if offset is None:
            raise ModelValidationError(f"No offset sent with data to write to file {file_id}")
        if chunk_size is None:
            raise ModelValidationError(f"No chunk_size sent with data to write to file {file_id}")

        n = int(int(offset) / int(chunk_size))
        self._save_chunk(file_id, n, chunk_size, b64decode(data).decode('utf-8'))


class FileNameAPI(BaseHandler):
    def _save_file(self, file_name):
        f = File(file_name=file_name)
        f = db.create(f)
        return f.id

    @authenticated(permissions=[Permissions.READ])
    def get(self):

        """
        ---
        summary: Retrieve a specific file
        parameters:
          - name: file_name
            in: query
            required: true
            description: The name of the file being sent
        responses:
          200:
            description: File name to post with
            schema:
              $ref: '#/definitions/Request'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_name = self.get_query_argument('file_name', default="")
        self.write(self._save_file(file_name))
