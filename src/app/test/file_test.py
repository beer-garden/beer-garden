# -*- coding: utf-8 -*-
from base64 import b64decode, b64encode

import pytest
from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import (
    File,
    FileChunk,
    FileStatus,
    FileTrigger,
    Job,
    Request,
    RequestTemplate,
)
from mock import Mock
from mongoengine.fields import ObjectIdField

import beer_garden.db.api as db
import beer_garden.files as files
from beer_garden.errors import NotUniqueException


class TestFileOperations(object):
    @pytest.fixture
    def simple_data(self):
        return "abcedfghijklmnopqrstuvwxyz1234567890,./;'[]`-="

    @pytest.fixture
    def base64_data(self, simple_data):
        return b64encode(bytes(simple_data, "utf-8"))

    @pytest.fixture
    def simple_file(self, base64_data):
        return File(
            file_name="my_test_data.txt",
            file_size=len(base64_data) * 4,
            chunk_size=len(base64_data),
            id=str(ObjectIdField().to_python(None)),
            owner_type=None,
            owner_id=None,
            request=None,
            job=ObjectIdField().to_python(None),
            chunks={
                "0": str(ObjectIdField().to_python(None)),
                "1": str(ObjectIdField().to_python(None)),
                "2": str(ObjectIdField().to_python(None)),
                "3": str(ObjectIdField().to_python(None)),
            },
        )

    @pytest.fixture
    def simple_file_chunk(self, simple_file, base64_data):
        return FileChunk(
            id=str(ObjectIdField().to_python(None)),
            file_id=simple_file.id,
            data=base64_data,
        )

    @pytest.fixture
    def storage_create_kwargs(self):
        return {"owner_id": "Doesn't matter", "owner_type": "Storage"}

    @pytest.fixture
    def modified_file(self, simple_file):
        return File(
            file_name="another_file_name.txt",
            file_size=1024 * 1024,
            chunk_size=1024,
            id=simple_file.id,
        )

    def test_file_create(
        self, monkeypatch, simple_file, modified_file, simple_file_chunk
    ):
        query_mock = Mock()
        monkeypatch.setattr(db, "query_unique", query_mock)
        create_mock = Mock()
        monkeypatch.setattr(db, "create", create_mock)
        monkeypatch.setattr(db, "modify", Mock(return_value=modified_file))

        create_mock.side_effect = iter(
            [
                simple_file,
            ]
        )
        file_status = files.create_file(
            simple_file.file_name, simple_file.file_size, simple_file.chunk_size
        )
        assert simple_file.id in file_status.file_id

        # Exercising the upsert flag logic
        create_mock.side_effect = iter(
            [
                NotUniqueException(),
            ]
        )
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

        # Using the upsert flag should allow us to update some of the metadata
        query_mock.side_effect = iter([simple_file, modified_file])
        try:
            files.create_file(
                modified_file.file_name,
                modified_file.file_size,
                modified_file.chunk_size,
                file_id=simple_file.id,
                upsert=True,
            )
        except NotUniqueException:
            raise AssertionError()

        # Testing the max chunk size check
        try:
            # Making chunk sizes too big to fit in the DB should be blocked
            files.create_file(
                modified_file.file_name,
                modified_file.file_size * 1024 * 1024,
                modified_file.chunk_size * 1024 * 1024,
                file_id=str(ObjectIdField().to_python(None)),
            )
            raise AssertionError()
        except ValueError:
            pass

        # Testing chunk creation with upsert
        for x in range(len(simple_file.chunks)):
            query_mock.side_effect = iter([simple_file, simple_file])
            create_mock.side_effect = iter(
                [
                    simple_file_chunk,
                ]
            )
            files.create_chunk(simple_file.id, x, simple_file_chunk.data, upsert=True)

        # Fill out the metadata now
        query_mock.side_effect = iter([simple_file, modified_file])
        create_mock.side_effect = iter(
            [
                simple_file_chunk,
            ]
        )
        assert files.create_file(
            modified_file.file_name,
            modified_file.file_size,
            modified_file.chunk_size,
            modified_file.id,
            upsert=True,
        ).operation_complete

    def test_file_fetch(self, monkeypatch, simple_file, simple_file_chunk):
        query_mock = Mock()
        monkeypatch.setattr(db, "query_unique", query_mock)

        # Read the data in its entirety
        query_mock.side_effect = iter(
            [
                simple_file,
                simple_file,
                simple_file_chunk,
                simple_file_chunk,
                simple_file_chunk,
                simple_file_chunk,
            ]
        )
        meta = files.fetch_file(simple_file.id)
        assert b64decode(meta.data).decode("utf-8") == b64decode(
            simple_file_chunk.data
        ).decode("utf-8") * len(simple_file.chunks)

        # Read the data chunk by chunk
        my_data = ""
        for x in range(len(simple_file.chunks)):
            query_mock.side_effect = iter(
                [
                    simple_file,
                    simple_file_chunk,
                ]
            )
            my_data += b64decode(
                (files.fetch_file(simple_file.id, chunk=x)).data
            ).decode("utf-8")
        assert my_data == b64decode(simple_file_chunk.data).decode("utf-8") * len(
            simple_file.chunks
        )

    def test_file_query(self, monkeypatch, base64_data, simple_file):
        query_mock = Mock()
        monkeypatch.setattr(db, "query_unique", query_mock)

        # Checking id formatting
        try:
            files.delete_file("my_invalid_id")
        except ModelValidationError:
            pass

        # Checking id correctness
        query_mock.side_effect = iter([None])
        try:
            files.delete_file("ffffeeeeddddccccbbbbaaaa")
        except NotFoundError:
            pass

    @pytest.fixture
    def simple_request(self):
        return Request(
            system="something_v3",
            system_version="3.0.0",
            instance_name="my_bg",
            namespace="file_testing",
            command="something_cool",
            id=str(ObjectIdField().to_python(None)),
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
            id=str(ObjectIdField().to_python(None)),
        )

    @pytest.fixture
    def custom_owner(self, simple_file):
        return File(
            file_name=simple_file.file_name,
            file_size=simple_file.file_size,
            chunk_size=simple_file.chunk_size,
            id=simple_file.id,
            owner_type="MY_CUSTOM_TYPE",
            owner_id="MY_CUSTOM_ID",
        )

    @pytest.fixture
    def req_owner(self, simple_file, simple_request):
        return File(
            file_name=simple_file.file_name,
            file_size=simple_file.file_size,
            chunk_size=simple_file.chunk_size,
            id=simple_file.id,
            owner_type="REQUEST",
            owner_id=simple_request.id,
            request=ObjectIdField().to_python(None),
        )

    @pytest.fixture
    def job_owner(self, simple_file, simple_job):
        return File(
            file_name=simple_file.file_name,
            file_size=simple_file.file_size,
            chunk_size=simple_file.chunk_size,
            id=simple_file.id,
            owner_type="JOB",
            owner_id=simple_job.id,
            job=ObjectIdField().to_python(None),
        )

    def test_file_owner(
        self,
        monkeypatch,
        simple_data,
        simple_file,
        custom_owner,
        req_owner,
        job_owner,
        simple_request,
        simple_job,
    ):
        mod_mock = Mock()
        monkeypatch.setattr(db, "modify", mod_mock)
        monkeypatch.setattr(db, "create", Mock(return_value=simple_file))
        query_mock = Mock()
        monkeypatch.setattr(db, "query_unique", query_mock)

        num_chunks = 5
        chunk_len = len(simple_data)
        file_metadata = files.create_file(
            "my_test_data.txt", num_chunks * chunk_len, chunk_len
        )
        file_id = file_metadata.file_id
        assert file_id is not None

        # Lowest ownership priority
        query_mock.side_effect = iter(
            [
                custom_owner,
            ]
        )
        mod_mock.side_effect = iter(
            [
                custom_owner,
            ]
        )
        file_metadata = files.set_owner(
            file_id, owner_type=custom_owner.owner_type, owner_id=custom_owner.owner_id
        )
        assert file_metadata.owner_type == custom_owner.owner_type
        assert file_metadata.owner_id == custom_owner.owner_id

        # Next lowest ownership priority
        query_mock.side_effect = iter(
            [
                custom_owner,
                simple_request,
                req_owner,
            ]
        )
        mod_mock.side_effect = iter(
            [
                req_owner,
            ]
        )
        file_metadata = files.set_owner(
            file_id, owner_type="REQUEST", owner_id=simple_request.id
        )
        assert file_metadata.owner_type == "REQUEST"
        assert file_metadata.owner_id == simple_request.id

        # Highest ownership priority
        query_mock.side_effect = iter(
            [
                req_owner,
                simple_job,
            ]
        )
        mod_mock.side_effect = iter(
            [
                job_owner,
            ]
        )
        file_metadata = files.set_owner(
            file_id, owner_type="JOB", owner_id=simple_job.id
        )
        assert file_metadata.owner_type == "JOB"
        assert file_metadata.owner_id == simple_job.id

        # Make sure lower priority owners can't overwrite the field
        query_mock.side_effect = iter(
            [
                job_owner,
                job_owner,
            ]
        )
        assert not (
            files.set_owner(file_id, owner_type="REQUEST", owner_id=simple_request.id)
        ).operation_complete
        assert not (
            files.set_owner(
                file_id, owner_type="MY_CUSTOM_TYPE", owner_id="MY_CUSTOM_ID"
            )
        ).operation_complete

    def test_safe_build(self, simple_file, simple_file_chunk):
        status = files._safe_build_object(FileStatus, simple_file)
        assert status.file_name == simple_file.file_name
        assert status.file_size == simple_file.file_size
        assert not hasattr(status, "job")
        # Make sure that the ID field is set up correctly with the new name and format
        assert not hasattr(status, "id") and simple_file.id in status.file_id

        # Test the kwargs pass-through
        status = files._safe_build_object(
            FileStatus, simple_file, operation_complete=True, valid=False
        )
        assert status.operation_complete
        assert not status.valid
        assert status.chunk_size == simple_file.chunk_size

        # Test the ignore function
        status = files._safe_build_object(
            FileStatus, simple_file, ignore=["file_name", "file_size"]
        )
        assert status.file_name is None
        assert status.file_size is None
        assert status.chunk_size == simple_file.chunk_size

        # Test the multi-object function
        status = files._safe_build_object(FileStatus, simple_file, simple_file_chunk)
        assert (
            simple_file.id in status.file_id and status.chunk_id == simple_file_chunk.id
        )
        assert status.data == simple_file_chunk.data
        assert status.file_size == simple_file.file_size

        # Test building a dictionary
        my_dict = files._safe_build_object(dict, simple_file)
        assert simple_file.id in my_dict["file_id"]
        assert my_dict["file_size"] == simple_file.file_size
