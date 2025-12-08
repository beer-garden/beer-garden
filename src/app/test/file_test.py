# -*- coding: utf-8 -*-
from base64 import b64decode, b64encode

import pytest
from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import FileStatus
from mongoengine.fields import ObjectIdField

import beer_garden.files as files
from beer_garden.db.mongo.models import (
    File,
    FileChunk,
    FileTrigger,
    Job,
    Request,
    RequestTemplate,
)
from beer_garden.errors import NotUniqueException


@pytest.fixture(autouse=True)
def drop():
    yield
    File.drop_collection()
    FileChunk.drop_collection()


class TestFileOperations(object):

    @pytest.fixture
    def simple_data(self):
        return "abcedfghijklmnopqrstuvwxyz1234567890,./;'[]`-="

    @pytest.fixture
    def base64_data(self, simple_data):
        return b64encode(bytes(simple_data, "utf-8"))

    @pytest.fixture
    def simple_file(self, base64_data):
        file = File(
            file_name="my_test_data.txt",
            file_size=len(b64decode(base64_data)) * 4,
            chunk_size=len(b64decode(base64_data)),
            id=str(ObjectIdField().to_python(None)),
            owner_type=None,
            owner_id=None,
        )

        file.save()

        for x in range(4):
            chunk = FileChunk(
                offset=x,
                file_id=str(file.id),
                data=base64_data,
            )
            chunk.save()
            file.chunks[str(x)] = str(chunk.id)

        file.save()

        yield file

        for chunk in file.chunks.values():
            FileChunk.objects(id=chunk).delete()
        file.delete()

    def test_file_create_duplicate_id(self, simple_file):
        try:
            # Attempting to create a file with a reserved id and
            # no upsert flag should always throw an error
            files.create_file(
                simple_file.file_name,
                simple_file.file_size,
                simple_file.chunk_size,
                file_id=simple_file.id,
            )
            raise AssertionError()
        except NotUniqueException:
            pass

    def test_file_create_upsert_duplicate_id(self, simple_file):
        try:
            # Attempting to create a file with a reserved id and
            # no upsert flag should always throw an error
            files.create_file(
                simple_file.file_name,
                simple_file.file_size,
                simple_file.chunk_size,
                file_id=simple_file.id,
                upsert=True,
            )

        except NotUniqueException:
            raise AssertionError()

    def test_max_chunk_size(self, simple_file):
        try:
            # Making chunk sizes too big to fit in the DB should be blocked
            files.create_file(
                simple_file.file_name,
                simple_file.file_size * 1024 * 1024,
                simple_file.chunk_size * 1024 * 1024,
            )
            raise AssertionError()
        except ValueError:
            pass

    def test_upsert_chunk(self, simple_file, base64_data):
        for x in range(len(simple_file.chunks)):
            chunk = files.create_chunk(simple_file.id, x, base64_data, upsert=True)
            assert File.objects().get(id=simple_file.id).chunks[str(x)] == str(
                chunk.chunk_id
            )

    def test_file_fetch(self, simple_file, base64_data):

        meta = files.fetch_file(simple_file.id)
        assert b64decode(meta.data).decode("utf-8") == b64decode(base64_data).decode(
            "utf-8"
        ) * len(simple_file.chunks)

        # Read the data chunk by chunk
        my_data = ""
        for x in range(len(simple_file.chunks)):
            my_data += b64decode(
                (files.fetch_file(simple_file.id, chunk=x)).data
            ).decode("utf-8")
        assert my_data == b64decode(base64_data).decode("utf-8") * len(
            simple_file.chunks
        )

    def test_file_query(self, base64_data, simple_file):

        # Checking id formatting
        try:
            files.delete_file("my_invalid_id")
            raise AssertionError()
        except ModelValidationError:
            pass

        # Checking id correctness
        try:
            files.delete_file("ffffeeeeddddccccbbbbaaaa")
            raise AssertionError()
        except NotFoundError:
            pass

    @pytest.fixture
    def simple_request(self):
        request = Request(
            system="something_v3",
            system_version="3.0.0",
            instance_name="my_bg",
            namespace="file_testing",
            command="something_cool",
        )

        request.save()

        yield request
        request.delete()

    @pytest.fixture
    def simple_job(self):
        job = Job(
            trigger_type="file",
            trigger=FileTrigger(
                pattern="do_not_care",
                path="./",
                recursive=False,
                create=False,
                modify=False,
                move=False,
                delete=False,
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

        job.save()

        yield job
        job.delete()

    def test_set_owner(self, simple_file):
        # Test setting the owner
        file_metadata = files.set_owner(
            simple_file.id, owner_type="MY_CUSTOM_TYPE", owner_id="MY_CUSTOM_ID"
        )
        assert file_metadata.owner_type == "MY_CUSTOM_TYPE"
        assert file_metadata.owner_id == "MY_CUSTOM_ID"

        # Test setting the owner to None
        file_metadata = files.set_owner(simple_file.id)
        assert file_metadata.owner_type is None
        assert file_metadata.owner_id is None

    def test_set_owner_priority(self, simple_file, simple_request, simple_job):
        # Test setting the owner to a lower priority
        file_metadata = files.set_owner(
            simple_file.id, owner_type="REQUEST", owner_id=str(simple_request.id)
        )
        assert file_metadata.operation_complete
        assert file_metadata.owner_type == "REQUEST"
        assert file_metadata.owner_id == str(simple_request.id)

        # Test setting the owner to a higher priority
        file_metadata = files.set_owner(
            simple_file.id, owner_type="JOB", owner_id=str(simple_job.id)
        )
        assert file_metadata.operation_complete
        assert file_metadata.owner_type == "JOB"
        assert file_metadata.owner_id == str(simple_job.id)

        # Testing setting the owner to a lower priority
        file_metadata = files.set_owner(
            simple_file.id, owner_type="REQUEST", owner_id=str(simple_request.id)
        )
        assert not file_metadata.operation_complete

    def test_safe_build(self, simple_file):
        status = files._safe_build_object(
            FileStatus, files.check_file(str(simple_file.id))
        )
        assert status.file_name == simple_file.file_name
        assert status.file_size == simple_file.file_size
        assert not hasattr(status, "job")
        # Make sure that the ID field is set up correctly with the new name and format
        assert not hasattr(status, "id") and str(simple_file.id) in status.file_id

    def test_safe_build_with_kwargs(self, simple_file):
        # Test the kwargs pass-through
        status = files._safe_build_object(
            FileStatus,
            files.check_file(str(simple_file.id)),
            operation_complete=True,
            valid=False,
        )
        assert status.operation_complete
        assert not status.valid
        assert status.chunk_size == simple_file.chunk_size

    def test_safe_build_with_ignore(self, simple_file):
        # Test the ignore function
        status = files._safe_build_object(
            FileStatus,
            files.check_file(str(simple_file.id)),
            ignore=["file_name", "file_size"],
        )
        assert status.file_name is None
        assert status.file_size is None
        assert status.chunk_size == simple_file.chunk_size

    def test_safe_build_dictonary(self, simple_file):

        # Test building a dictionary
        my_dict = files._safe_build_object(dict, files.check_file(str(simple_file.id)))
        assert str(simple_file.id) in my_dict["file_id"]
        assert my_dict["file_size"] == simple_file.file_size
