# -*- coding: utf-8 -*-
import os
from uuid import uuid4
from mimetypes import guess_type

import tornado.web
from tornado.iostream import PipeIOStream

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler, event_wait
from brewtils.errors import ModelValidationError

BASEDIR_NAME = os.path.dirname(__file__)
BASEDIR_PATH = os.path.abspath(BASEDIR_NAME)
FILES_ROOT = os.path.join(BASEDIR_PATH, 'files')

MAX_STREAM_SIZE = 1024 * 1024 * 1024

print(f"~~~~~~~~~~~~~~~~~~~~~~~~~FILE ROOT PATH: {FILES_ROOT}")


class FileAPI(BaseHandler):
    # def initialize(self):
    #     self.stream = None
    #
    # def prepare(self):
    #     super().prepare()
    #
    #     if self.stream is None:
    #         full_file_name = os.path.join(FILES_ROOT, str(uuid4()))
    #         print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Creating file name {full_file_name}")
    #         fp = os.open(full_file_name, os.O_CREAT | os.O_WRONLY)
    #         # This allows async behavior
    #         self.stream = PipeIOStream(fp)
    #     self.request.connection.set_max_body_size(MAX_STREAM_SIZE)
    #
    # async def data_received(self, chunk):
    #     print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Received stream data!")
    #     await self.stream.write(chunk)

    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve a specific file
        parameters:
          - name: file_name
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
        file_name = self.get_query_argument("file_name", default=None)
        file_location = os.path.join(FILES_ROOT, file_name)
        if not os.path.isfile(file_location):
            raise tornado.web.HTTPError(status_code=404)
        content_type, _ = guess_type(file_location)
        self.set_header('Content-Type', content_type)
        with open(file_location) as source_file:
            self.write(source_file.read())

    @authenticated(permissions=[Permissions.CREATE])
    async def post(self):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: file_name
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
        print("~~~~~~~~~~~~~~~~~~~~RECEIVED POST")
        file_name = self.get_query_argument("file_name", default=None)
        data = self.get_body_argument("data", default=None)
        offset = self.get_body_argument("offset", default=None)

        if data is None:
            raise ModelValidationError(f"No data sent to write to file {file_name}")
        if offset is None:
            raise ModelValidationError(f"No offset sent with data to write to file {file_name}")

        full_file_name = os.path.join(FILES_ROOT, file_name+"_"+offset)
        with open(full_file_name, 'w') as fp:
            fp.write(data)


class FileNameAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    def get(self):

        """
        ---
        summary: Retrieve a specific file
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

        self.write(str(uuid4()))