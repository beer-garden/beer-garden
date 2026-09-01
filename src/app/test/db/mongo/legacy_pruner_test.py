# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from mongoengine.connection import get_db

import beer_garden
from beer_garden import config
from beer_garden.db.mongo.legacy_pruner import (
    prune_action_requests,
    prune_admin_requests,
    prune_files,
    prune_grid_fs,
    prune_info_requests,
    prune_missed_temp_command,
    prune_orphan_files,
    prune_temp_requests,
)
from beer_garden.db.mongo.models import (
    DateTrigger,
    File,
    Job,
    RawFile,
    Request,
    RequestTemplate,
)

FAKE_TIME = datetime.datetime.now(timezone.utc) + timedelta(minutes=60)


@pytest.fixture
def collection_mock():
    return MagicMock(__name__="MOCK")


@pytest.fixture
def task(collection_mock):
    return {
        "collection": collection_mock,
        "field": "test",
        "batch_size": -1,
        "delete_after": timedelta(microseconds=1),
        "additional_query": Mock(),
    }


@pytest.fixture
def action_request():
    action_req = Request(
        system="T",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="SUCCESS",
        command_type="ACTION",
    )
    action_req.save()
    yield action_request
    action_req.delete()


@pytest.fixture
def info_request():
    info_req = Request(
        system="T",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="SUCCESS",
        command_type="INFO",
    )
    info_req.save()
    yield info_request
    info_req.delete()


@pytest.fixture
def admin_request():
    admin_req = Request(
        system="T",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="SUCCESS",
        command_type="ADMIN",
    )
    admin_req.save()
    yield admin_request
    admin_req.delete()


@pytest.fixture
def temp_request():
    temp_req = Request(
        system="T",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="SUCCESS",
        command_type="TEMP",
    )
    temp_req.save()
    yield temp_request
    temp_req.delete()


@pytest.fixture
def file():
    file_obj = File(
        owner_id="T",
        file_name="T",
        file_size=1,
        chunk_size=1,
        updated_at=datetime.datetime(2024, 1, 17),
    )
    file_obj.save()
    yield file
    file_obj.delete()


@pytest.fixture()
def raw_file():
    rawfile = RawFile()
    rawfile.file.put(b"test", filename="test.txt")
    rawfile.save()
    yield rawfile
    rawfile.delete()


@pytest.fixture
def in_progress():
    in_progress = Request(
        system="T",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="IN_PROGRESS",
    )
    in_progress.save()
    yield in_progress
    in_progress.delete()


@pytest.fixture
def created():
    created = Request(
        system="T1",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="CREATED",
    )
    created.save()
    yield created
    created.delete()


@pytest.fixture
def canceled():
    canceled = Request(
        system="T1",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2024, 1, 17),
        status="CANCELED",
    )
    canceled.save()
    yield canceled
    canceled.delete()


class TestMongoPruner(object):
    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_prune_info_requests(self, mock_datetime, info_request):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"info": 1}}}}
        prune_info_requests()
        assert len(Request.objects.filter(command_type="INFO")) == 0

    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_prune_info_requests_children(self, mock_datetime):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"info": 1}}}}

        grandparent = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="G",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(minutes=60),
            status="SUCCESS",
            command_type="INFO",
        )
        grandparent.save()

        parent = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="P",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(minutes=60),
            status="SUCCESS",
            command_type="INFO",
            has_parent=True,
            parent_id=str(grandparent.id),
        )
        parent.save()

        child = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="C",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(minutes=60),
            status="SUCCESS",
            command_type="INFO",
            has_parent=True,
            parent_id=str(parent.id),
        )
        child.save()

        prune_info_requests()
        assert len(Request.objects.filter(command_type="INFO")) == 0

    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_prune_action_requests(self, mock_datetime, action_request):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 1}}}}
        prune_action_requests()
        assert len(Request.objects.filter(command_type="ACTION")) == 0

    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_prune_action_request_no_command_type(
        self, mock_datetime, in_progress, created, canceled
    ):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 1}}}}
        prune_action_requests()
        assert len(Request.objects.filter(command_type="ACTION")) == 0
        assert len(Request.objects.filter(command_type=None)) == 2

    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_prune_admin_requests(self, mock_datetime, admin_request):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 15}}}
        prune_admin_requests()
        assert len(Request.objects.filter(command_type="ADMIN")) == 0

    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_prune_temp_requests(self, mock_datetime, temp_request):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 15}}}
        prune_temp_requests()
        assert len(Request.objects.filter(command_type="TEMP")) == 0

    def test_prune_files(self, file, raw_file):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"file": 1}}}}
        prune_files()
        assert len(File.objects.all()) == 0

    def test_skip_prune_request_gridfs_files(self, monkeypatch):
        db = get_db()

        db["request"].delete_many({})
        db["fs.files"].delete_many({})
        db["fs.chunks"].delete_many({})

        config._CONFIG = {
            "db": {
                "prune": {
                    "batch_size": -1,
                    "ttl": {"file": 1, "info": -1, "action": -1},
                }
            }
        }

        FAKE_TIME = datetime.datetime.now(timezone.utc) + timedelta(minutes=60)

        class mydatetime(datetime.datetime):
            @classmethod
            def now(cls, *arg, **kwargs):
                return FAKE_TIME

        monkeypatch.setattr(beer_garden.db.mongo.legacy_pruner, "datetime", mydatetime)

        request = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            # created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="ACTION",
        )
        request.output_gridfs.put(b"test", filename="test.txt")
        request.parameters_gridfs.put(b"test", filename="test.txt")
        request.save()

        # Orphaned Gridfs files
        assert db["fs.files"].count_documents({}) == 2
        assert db["fs.chunks"].count_documents({}) == 2

        prune_grid_fs()
        assert db["fs.files"].count_documents({}) == 2
        assert db["fs.chunks"].count_documents({}) == 2
        db["request"].delete_many({})
        db["fs.files"].delete_many({})
        db["fs.chunks"].delete_many({})

    def test_prune_request_gridfs_files(self, monkeypatch):
        db = get_db()

        db["request"].delete_many({})
        db["fs.files"].delete_many({})
        db["fs.chunks"].delete_many({})

        config._CONFIG = {
            "db": {
                "prune": {
                    "batch_size": -1,
                    "ttl": {"file": 1, "info": -1, "action": -1},
                }
            }
        }

        FAKE_TIME = datetime.datetime.now(timezone.utc) + timedelta(minutes=60)

        class mydatetime(datetime.datetime):
            @classmethod
            def now(cls, *arg, **kwargs):
                return FAKE_TIME

        monkeypatch.setattr(beer_garden.db.mongo.legacy_pruner, "datetime", mydatetime)

        request = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            # created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="ACTION",
        )
        request.output_gridfs.put(b"test", filename="test.txt")
        request.parameters_gridfs.put(b"test", filename="test.txt")
        request.save()

        db["request"].delete_one({})
        # Orphaned Gridfs files
        assert db["fs.files"].count_documents({}) == 2
        assert db["fs.chunks"].count_documents({}) == 2

        prune_grid_fs()
        assert db["fs.files"].count_documents({}) == 0
        assert db["fs.chunks"].count_documents({}) == 0

    def test_prune_raw_file_gridfs_files(self, monkeypatch):
        db = get_db()

        db["raw_file"].delete_many({})
        db["fs.files"].delete_many({})
        db["fs.chunks"].delete_many({})

        config._CONFIG = {
            "db": {
                "prune": {
                    "batch_size": -1,
                    "ttl": {"file": 1, "info": -1, "action": -1},
                }
            }
        }

        FAKE_TIME = datetime.datetime.now(timezone.utc) + timedelta(minutes=60)

        class mydatetime(datetime.datetime):
            @classmethod
            def now(cls, *arg, **kwargs):
                return FAKE_TIME

        monkeypatch.setattr(beer_garden.db.mongo.legacy_pruner, "datetime", mydatetime)

        rawfile = RawFile()
        rawfile.file.put(b"test", filename="test.txt")
        rawfile.save()

        db["raw_file"].delete_one({})
        # Orphaned Gridfs files
        assert db["fs.files"].count_documents({}) == 1
        assert db["fs.chunks"].count_documents({}) == 1

        prune_grid_fs()
        assert db["fs.files"].count_documents({}) == 0
        assert db["fs.chunks"].count_documents({}) == 0


class TestMissedTempPruner(object):
    @pytest.fixture
    def missed_child_request(self):
        parent = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="ACTION",
        )
        parent.save()

        child = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="TEMP",
            has_parent=True,
            parent_id=str(parent.id),
        )

        # parent.delete()
        child.save()

        yield child
        parent.delete()
        child.delete()

    @pytest.fixture
    def valid_child_request(self):
        parent = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime(2024, 1, 17),
            status="IN_PROGRESS",
            command_type="ACTION",
        )
        parent.save()

        child = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="TEMP",
            has_parent=True,
            parent_id=str(parent.id),
        )

        # parent.delete()
        child.save()

        yield child
        parent.delete()
        child.delete()

    @patch("beer_garden.db.mongo.legacy_pruner.datetime")
    def test_missed_temp_pruner(self, mock_datetime, missed_child_request):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 1}}}
        assert len(Request.objects.filter(command_type="TEMP")) == 1

        prune_missed_temp_command()
        assert len(Request.objects.filter(command_type="TEMP")) == 0

    def test_valid_temp_pruner(self, valid_child_request):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 1}}}
        assert len(Request.objects.filter(command_type="TEMP")) == 1

        prune_missed_temp_command()
        assert len(Request.objects.filter(command_type="TEMP")) == 1


class TestOrphanFile(object):

    @pytest.fixture
    def orphan_request_file(self):

        owner = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="ACTION",
        )
        owner.save()

        file = File(
            owner_id=str(owner.id),
            file_name="T",
            file_size=1,
            chunk_size=1,
            updated_at=datetime.datetime(2024, 1, 17),
            owner_type="REQUEST",
            request=owner,
        )

        owner.delete()
        file.save()

        yield file

        file.delete()

    @pytest.fixture
    def orphan_job_file(self, ts_dt, request_template_dict):

        owner = Job(
            name="T",
            trigger_type="date",
            trigger=DateTrigger(run_date=ts_dt),
            request_template=RequestTemplate(**request_template_dict),
        )

        owner.save()

        file = File(
            owner_id=str(owner.id),
            file_name="T",
            file_size=1,
            chunk_size=1,
            updated_at=datetime.datetime(2024, 1, 17),
            owner_type="JOB",
            job=owner,
        )

        owner.delete()
        file.save()

        yield file

        file.delete()

    @pytest.fixture
    def deleted_request_file(self):

        owner = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime(2024, 1, 17),
            status="SUCCESS",
            command_type="ACTION",
        )
        owner.save()

        file = File(
            owner_id=str(owner.id),
            file_name="T",
            file_size=1,
            chunk_size=1,
            updated_at=datetime.datetime(2024, 1, 17),
            owner_type="REQUEST",
            request=owner,
        )

        file.save()
        owner.delete()

        yield file

        file.delete()

    @pytest.fixture
    def deleted_job_file(self, ts_dt, request_template_dict):

        owner = Job(
            name="T",
            trigger_type="date",
            trigger=DateTrigger(run_date=ts_dt),
            request_template=RequestTemplate(**request_template_dict),
        )

        owner.save()

        file = File(
            owner_id=str(owner.id),
            file_name="T",
            file_size=1,
            chunk_size=1,
            updated_at=datetime.datetime(2024, 1, 17),
            owner_type="JOB",
            job=owner,
        )

        file.save()
        owner.delete()

        yield file

        file.delete()

    def test_orphan_file(self, orphan_request_file, deleted_request_file):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 1}}}
        assert len(File.objects.all()) == 2

        prune_orphan_files()
        assert len(File.objects.all()) == 1

    def test_orphan_job(self, orphan_job_file, deleted_job_file):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 1}}}
        assert len(File.objects.all()) == 2

        prune_orphan_files()
        assert len(File.objects.all()) == 1
