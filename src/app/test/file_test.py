# -*- coding: utf-8 -*-
import pytest
from random import choice
from mongoengine import disconnect

import beer_garden
import beer_garden.files as files
import beer_garden.db.api as db
from beer_garden.errors import NotUniqueException
from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import File, FileChunk, Request, Job, FileTrigger, RequestTemplate


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
        disconnect(alias="default")

    @pytest.fixture
    def simple_data(self):
        return "".join(
            [
                choice("abcedfghijklmnopqrstuvwxyz1234567890,./;'[]`-=")
                for x in range(256)
            ]
        )

    @pytest.fixture
    def storage_create_kwargs(self):
        return {"owner_id": "Doesn't matter", "owner_type": "Storage"}

    @pytest.fixture
    def simple_request(self):
        return Request(
            system="something_v3",
            system_version="3.0.0",
            instance_name="my_bg",
            namespace="file_testing",
            command="something_cool",
        )

    @pytest.fixture
    def simple_job(self):
        return Job(
            trigger_type="file",
            trigger=FileTrigger(
                pattern="do_not_care", path="./", callbacks={"on_created": True}
            ),
            request_template=RequestTemplate(
                system="something_v3",
                system_version="3.0.0",
                instance_name="my_bg",
                namespace="file_testing",
                command="something_cool",
            ),
            name="my_simple_job",
        )

    def test_file_create(self, simple_data):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_status = files.create_file(
            "my_test_data.txt", num_chunks * chunk_len, chunk_len
        )
        file_id = file_status.file_id
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
            meta = files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id=file_id,
                upsert=True,
            )
            files.delete_file(meta.file_id)
        except NotUniqueException:
            assert False

        # Test the id checking logic
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
            meta = files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id="123456789012345678901234",
            )
            files.delete_file(meta.file_id)
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

        # Testing chunk creation with upsert
        for x in range(num_chunks):
            files.create_chunk(file_id, x, simple_data, upsert=True)

        # Fill out the metadata now
        assert (
            files.create_file(
                "my_other_test_data.txt",
                num_chunks * chunk_len,
                chunk_len,
                file_id=file_id,
                upsert=True,
            )
            is not None
        )

        # Cleanup! (again)
        files.delete_file(file_id)

    def test_file_fetch(self, simple_data):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = files.create_file(
            "my_test_data.txt", num_chunks * chunk_len, chunk_len
        )
        file_id = file_metadata.file_id
        assert file_id is not None

        # Upload some data
        chunk_ids = []
        for x in range(num_chunks):
            chunk_meta = files.create_chunk(file_id, x, simple_data)
            chunk_ids.append(chunk_meta.chunk_id)
        assert len(chunk_ids) == num_chunks

        # Read the data in its entirety
        meta = files.fetch_file(file_id)
        assert meta.data == simple_data * num_chunks

        # Read the data chunk by chunk
        my_data = ""
        for x in range(num_chunks):
            my_data += (files.fetch_file(file_id, chunk=x)).data
        assert my_data == simple_data * num_chunks

        # Cleanup!
        files.delete_file(file_id)

    def test_file_delete(self, simple_data):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = files.create_file(
            "my_test_data.txt", num_chunks * chunk_len, chunk_len
        )
        file_id = file_metadata.file_id
        # We don't normally need to do this, but we're interacting directly with the DB
        file_id = file_id.split(" ")[1]
        assert file_id is not None

        # Upload some data
        chunk_ids = []
        for x in range(num_chunks):
            chunk_meta = files.create_chunk(file_id, x, simple_data)
            chunk_ids.append(chunk_meta.chunk_id)
        assert len(chunk_ids) == num_chunks

        # Checking id formatting
        try:
            files.delete_file("my_invalid_id")
        except ModelValidationError:
            pass

        # Checking id correctness
        try:
            files.delete_file("ffffeeeeddddccccbbbbaaaa")
        except NotFoundError:
            pass

        # Confirm our file is there
        assert db.query_unique(File, id=file_id) is not None
        for c_id in chunk_ids:
            assert db.query_unique(FileChunk, id=c_id) is not None

        # Make sure everything is deleted (including the chunks)
        assert files.delete_file(file_id) is not None
        for c_id in chunk_ids:
            assert db.query_unique(FileChunk, id=c_id) is None

    def test_file_owner(self, simple_data, simple_request, simple_job):
        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = files.create_file(
            "my_test_data.txt", num_chunks * chunk_len, chunk_len
        )
        file_id = file_metadata.file_id
        assert file_id is not None

        # Lowest ownership priority
        file_metadata = files.set_owner(
                file_id, owner_type="MY_CUSTOM_TYPE", owner_id="MY_CUSTOM_ID"
            )
        assert file_metadata.owner_type == "MY_CUSTOM_TYPE"
        assert file_metadata.owner_id == "MY_CUSTOM_ID"

        # Next lowest ownership priority
        req = db.create(simple_request)
        file_metadata = files.set_owner(file_id, owner_type="REQUEST", owner_id=req.id)
        assert file_metadata.owner_type == "REQUEST"
        assert file_metadata.owner_id == req.id

        # Highest ownership priority
        job = db.create(simple_job)
        file_metadata = files.set_owner(file_id, owner_type="JOB", owner_id=job.id)
        assert file_metadata.owner_type == "JOB"
        assert file_metadata.owner_id == job.id

        # Make sure lower priority owners can't overwrite the field
        assert not (
            files.set_owner(file_id, owner_type="REQUEST", owner_id=req.id)
        ).operation_complete
        assert not (
            files.set_owner(
                file_id, owner_type="MY_CUSTOM_TYPE", owner_id="MY_CUSTOM_ID"
            )
        ).operation_complete

        db.delete(req)
        db.delete(job)
        # Cleanup!
        files.delete_file(file_id)
