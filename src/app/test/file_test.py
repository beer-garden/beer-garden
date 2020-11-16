# -*- coding: utf-8 -*-
import pytest
from json import loads
from mongoengine import disconnect

import beer_garden
import beer_garden.files as files
import beer_garden.db.api as db
from beer_garden.errors import NotUniqueException
from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import File, FileChunk


class TestFileOperations(object):
    @classmethod
    def setup_class(cls):
        conf = {
            "name": "bg_file_test",
            "connection": {
                "host": "localhost",
                "password": None,
                "port": 27017,
                "username": None,
            },
            "ttl": {"action": -1, "info": 15},
        }
        db.create_connection(connection_alias="default", db_config=conf)

    @classmethod
    def teardown_class(cls):
        # Make sure we cleanup the DB!
        my_files = db.query(File)
        for f in my_files:
            db.delete(f)

        disconnect(alias="default")

    @pytest.fixture
    def simple_data(self):
        return "MY TEST DATA, MY TEST DATA, MY TEST DATA"

    @pytest.fixture
    def storage_create_kwargs(self):
        return {"owner_id": "Doesn't matter", "owner_type": "Storage"}

    def test_file_create(self, simple_data):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = loads(
            files.create_file("my_test_data.txt", num_chunks * chunk_len, chunk_len)
        )
        file_id = file_metadata["id"]
        assert file_id is not None

        # Exercising the upsert flag logic
        try:
            # Attempting to create a file with a reserved id and no upsert flag should always throw an error
            files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id=file_id,
            )
            assert False
        except NotUniqueException:
            pass

        try:
            # Using the upsert flag should allow us to update some of the metadata
            files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id=file_id,
                upsert=True,
            )
        except NotUniqueException:
            assert False

        #       # Test the id checking logic
        try:
            # The file ID passed should be required to be a ObjectId string
            files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id="my_invalid_id",
            )
            assert False
        except ModelValidationError:
            pass

        try:
            # The file ID passed should be required to be a ObjectId string (24 character hex string)
            files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id="123456789012345678901234",
            )
        except ModelValidationError:
            assert False

        # Testing the max chunk size check
        try:
            # Making chunk sizes too big to fit in the DB should be blocked
            files.create_file(
                "my_other_test_data.txt",
                1024 * 1024 * 1024,
                1024 * 1024 * 1024,
                file_id="123456789012345678901234",
            )
            assert False
        except ValueError:
            pass

    def test_file_fetch(self, simple_data):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = loads(
            files.create_file("my_test_data.txt", num_chunks * chunk_len, chunk_len)
        )
        file_id = file_metadata["id"]
        assert file_id is not None

        # Upload some data
        chunk_ids = []
        for x in range(num_chunks):
            chunk_meta = loads(files.create_chunk(file_id, x, simple_data))
            assert "id" in chunk_meta
            chunk_ids.append(chunk_meta["id"])
        assert len(chunk_ids) == num_chunks

        # Read the data in its entirety
        my_data = files.fetch_file(file_id)
        assert my_data == simple_data * num_chunks

        # Read the data chunk by chunk
        my_data = ""
        for x in range(num_chunks):
            my_data += files.fetch_file(file_id, chunk=x)
        assert my_data == simple_data * num_chunks

    def test_file_delete(self, simple_data):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = loads(
            files.create_file("my_test_data.txt", num_chunks * chunk_len, chunk_len)
        )
        file_id = file_metadata["id"]
        # We don't normally need to do this, but we're interacting directly with the DB
        file_id = file_id.split(" ")[1]
        assert file_id is not None

        # Upload some data
        chunk_ids = []
        for x in range(num_chunks):
            chunk_meta = loads(files.create_chunk(file_id, x, simple_data))
            assert "id" in chunk_meta
            chunk_ids.append(chunk_meta["id"])
        assert len(chunk_ids) == num_chunks

        # Checking id formatting
        assert files.delete_file("my_invalid_id") is None

        # Checking id correctness
        assert files.delete_file("ffffeeeeddddccccbbbbaaaa") is None

        # Confirm our file is there
        assert db.query_unique(File, id=file_id) is not None
        for c_id in chunk_ids:
            assert db.query_unique(FileChunk, id=c_id) is not None

        # Make sure everything is deleted (including the chunks)
        assert files.delete_file(file_id) is not None
        for c_id in chunk_ids:
            assert db.query_unique(FileChunk, id=c_id) is None
