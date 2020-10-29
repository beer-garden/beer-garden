# -*- coding: utf-8 -*-
import os
from base64 import b64decode
from math import ceil
from json import dumps

import tornado.web

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler, event_wait
import beer_garden.db.api as db
from brewtils.errors import ModelValidationError
from brewtils.models import File, FileChunk

# 10MB
MAX_CHUNK_SIZE = 1024 * 1024 * 10


def check_file(func):
    def wrapper(*args, **kwargs):
        file_id = args[1]
        res = db.query_unique(File, id=file_id)
        if res is None:
            raise ModelValidationError(f"Tried to fetch an unsaved file {file_id}.")
        new_args = list(args)
        new_args[1] = res
        return func(*new_args, **kwargs)
    return wrapper


def check_chunks(func):
    @check_file
    def wrapper(*args, **kwargs):
        res = args[1]
        if res.chunks is None:
            raise ModelValidationError(f"Tried to load a file {res.id} with no associated chunks.")
        return func(*args, **kwargs)
    return wrapper


class FileAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    def get(self):
        """
        ---
        summary: Retrieve a specific file
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
            type: string
          - name: verify
            in: query
            required: false
            description: Flag that will cause verification information to be returned instead of the file data
            type: bool
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
        chunk = self.get_query_argument("chunk", default=None)
        verify = bool(self.get_query_argument("verify", default=False))
        if file_id is None:
            raise ValueError("Cannot fetch a file or chunk without a file ID.")

        if verify:
            self.write(dumps(self._verify_chunks(file_id)))
        if chunk is not None:
            self.write(self._fetch_chunk(file_id, chunk))
        else:
            verification_dict = self._verify_chunks(file_id)
            if verification_dict['valid']:
                self.write(self._fetch_file(file_id))
            else:
                raise ModelValidationError(f"File {file_id} is incomplete {verification_dict}.")

    @check_chunks
    def _verify_chunks(self, file):
        num_chunks = ceil(file.file_size / file.chunk_size)
        computed_size = file.chunk_size * num_chunks

        length_ok = num_chunks == len(file.chunks)
        size_ok = file.file_size <= computed_size <= file.file_size + file.chunk_size

        missing = [x for x in range(len(file.chunks))
                   if file.chunks.get(str(x), None) is None]
        return {'valid': (length_ok and missing == [] and size_ok), 'missing': missing}

    @check_chunks
    def _fetch_chunk(self, file, chunk_num):
        if chunk_num in file.chunks:
            chunk = db.query_unique(FileChunk, id=file.chunks[chunk_num])
            if chunk is None:
                raise FileNotFoundError(f"Chunk number {chunk_num} was "
                                        f"indexed for file {file.id}, but could not be fetched")
            return chunk.data
        else:
            raise ValueError(f"Chunk number {chunk_num} is invalid for file {file.id}")

    @check_chunks
    def _fetch_file(self, file):
        # This is going to get big, try our best to be efficient
        all_data = [db.query_unique(FileChunk, id=file.chunks[str(x)]).data
                    for x in range(len(file.chunks))]
        return "".join(all_data)

    @check_file
    def _save_chunk(self, file, n=None, **meta_data):
        chunk = FileChunk(file_id=file.id, n=n, **meta_data)
        c = db.create(chunk)
        kwargs = {f'set__chunks__{n}': c.id}
        db.modify(file, **kwargs)

    @authenticated(permissions=[Permissions.CREATE])
    def post(self):
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
          - Files
        """
        file_id = self.get_query_argument("file_id", default=None)

        args = tornado.escape.json_decode(self.request.body)
        data = args.get('data', None)
        offset = args.get('offset', None)

        if file_id is None:
            raise ModelValidationError(f"No file id provided.")
        if data is None:
            raise ModelValidationError(f"No data sent to write to file {file_id}")
        if offset is None:
            raise ModelValidationError(f"No offset sent with data to write to file {file_id}")

        self._save_chunk(file_id, n=offset, data=b64decode(data).decode('utf-8'))

    @check_chunks
    def _delete_file(self, file):
        # Get rid of all of the chunks first
        for chunk_id in file.chunks.values():
            chunk = db.query_unique(FileChunk, id=chunk_id)
            if chunk is not None:
                db.delete(chunk)
        # Delete the parent file object
        db.delete(file)

    def delete(self):
        """
        ---
        summary: Create a new Request
        parameters:
          - name: file_id
            in: query
            required: true
            description: The ID of the file
            type: string
        responses:
          200:
            description: A new Request has been created
            schema:
              $ref: '#/definitions/Request'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Files
        """
        file_id = self.get_query_argument("file_id", default=None)
        if file_id is None:
            raise ValueError("Cannot delete a file without an id.")

        self._delete_file(file_id)


class FileNameAPI(BaseHandler):
    def _save_file(self, **meta_data):
        f = File(**meta_data)
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
          - name: chunk_size
            in: query
            required: true
            description: The size of chunks the file is being broken into (in bytes)
          - name: file_size
            in: query
            required: true
            description: The total size of the file (in bytes)
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
        chunk_size = self.get_query_argument('chunk_size', default=None)
        file_size = self.get_query_argument('file_size', default=None)

        if chunk_size is None:
            raise ModelValidationError(f"No chunk_size sent with file {file_name}.")
        if file_size is None:
            raise ModelValidationError(f"No file_size sent with file {file_name}.")

        try:
            if int(chunk_size) > MAX_CHUNK_SIZE:
                raise ModelValidationError(f"Cannot store file chunks larger than {MAX_CHUNK_SIZE} bytes.")
            meta_data = {'file_name': file_name, 'chunk_size': int(chunk_size), 'file_size': int(file_size)}
            self.write(self._save_file(**meta_data))
        except ValueError:
            raise ModelValidationError(f"Chunk size '{chunk_size}' or "
                                       f"File size '{file_size}' could not be converted to and integer")
