# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta, timezone

import pytest
from mock import MagicMock, Mock
from mongoengine.connection import get_db
from pymongo import UpdateOne

import beer_garden
from beer_garden import config
from beer_garden.db.mongo.models import (
    DateTrigger,
    File,
    Job,
    RawFile,
    Request,
    RequestTemplate,
)
from beer_garden.db.mongo.pruner import (
    find_missing_expiration_requests,
    prune_raw_files,
    prune_grid_fs,
    prune_files,
    prune_outstanding,
    prune_requests,
)
from mongomock.gridfs import enable_gridfs_integration

enable_gridfs_integration()


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
def clean_request():

    yield
    Request.drop_collection()


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
    def test_prune_info_requests(self, clean_request):

        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"info": 1}}}}
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
        assert len(Request.objects.filter(command_type="INFO")) == 1
        prune_requests()
        assert len(Request.objects.filter(command_type="INFO")) == 0

    def test_prune_action_requests(self, clean_request):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 1}}}}
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

        action_req = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime.now() + timedelta(days=1),
            status="SUCCESS",
            command_type="ACTION",
        )
        action_req.save()
        assert len(Request.objects.filter(command_type="ACTION")) == 2
        prune_requests()
        assert len(Request.objects.filter(command_type="ACTION")) == 1

    def test_prune_action_request_no_command_type(self, clean_request):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 1}}}}

        Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(days=1),
            status="IN_PROGRESS",
        ).save()

        Request(
            system="T1",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(days=1),
            status="CREATED",
        ).save()

        Request(
            system="T1",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(days=1),
            status="CANCELED",
        ).save()

        assert len(Request.objects.filter(command_type=None)) == 3

        assert len(Request.objects.filter(status="CREATED", expiration_at=None)) == 1
        assert (
            len(Request.objects.filter(status="IN_PROGRESS", expiration_at=None)) == 1
        )
        assert (
            len(Request.objects.filter(status="CANCELED", expiration_at__ne=None)) == 1
        )

        assert len(Request.objects.filter(command_type="ACTION")) == 0

        prune_requests()

        assert len(Request.objects.filter(command_type=None)) == 2

        assert len(Request.objects.filter(status="CREATED")) == 1
        assert len(Request.objects.filter(status="IN_PROGRESS")) == 1
        assert len(Request.objects.filter(status="CANCELED")) == 0

    def test_prune_admin_requests(self, admin_request):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 15}}}
        assert len(Request.objects.filter(command_type="ADMIN")) == 1
        prune_requests()
        assert len(Request.objects.filter(command_type="ADMIN")) == 0

    def test_prune_temp_requests(self, temp_request):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "interval": 15}}}
        assert len(Request.objects.filter(command_type="TEMP")) == 1
        prune_requests()
        assert len(Request.objects.filter(command_type="TEMP")) == 0

    def test_prune_raw_files(self, raw_file):
        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"file": 1}}}}
        prune_raw_files()
        assert len(RawFile.objects.all()) == 0

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

        monkeypatch.setattr(beer_garden.db.mongo.pruner, "datetime", mydatetime)

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
        assert db["fs.files"].count() == 2
        assert db["fs.chunks"].count() == 2

        prune_grid_fs()
        assert db["fs.files"].count() == 2
        assert db["fs.chunks"].count() == 2
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

        monkeypatch.setattr(beer_garden.db.mongo.pruner, "datetime", mydatetime)

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
        assert db["fs.files"].count() == 2
        assert db["fs.chunks"].count() == 2

        prune_grid_fs()
        assert db["fs.files"].count() == 0
        assert db["fs.chunks"].count() == 0

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

        monkeypatch.setattr(beer_garden.db.mongo.pruner, "datetime", mydatetime)

        rawfile = RawFile()
        rawfile.file.put(b"test", filename="test.txt")
        rawfile.save()

        db["raw_file"].delete_one({})
        # Orphaned Gridfs files
        assert db["fs.files"].count() == 1
        assert db["fs.chunks"].count() == 1

        prune_grid_fs()
        assert db["fs.files"].count() == 0
        assert db["fs.chunks"].count() == 0

    def test_run_cancels_outstanding_requests(self, task, in_progress, created):
        config._CONFIG = {
            "db": {"prune": {"in_progress_request_expiration": 1, "batch_size": -1}}
        }
        prune_outstanding()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "CANCELED"
        assert new_created.status == "CANCELED"
        assert (
            new_created.status_updated_at.date()
            == datetime.datetime.now(timezone.utc).date()
        )

    def test_negative_cancel_threshold(self, task, in_progress, created):
        config._CONFIG = {"db": {"prune": {"in_progress_request_expiration": -1}}}
        prune_outstanding()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "IN_PROGRESS"
        assert new_created.status == "CREATED"


class TestExpirationUpdater(object):

    def test_expiration_updater(self, clean_request):
        config._CONFIG = {
            "db": {"prune": {"batch_size": -1, "interval": 1, "ttl": {"action": 1}}}
        }

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
            command_type="ACTION",
            has_parent=True,
            parent=parent,
        )

        parent.delete()
        child.save()
        Request._get_collection().bulk_write(
            [
                UpdateOne(
                    {"_id": child.id},
                    {"$set": {"expiration_at": None}},
                )
            ],
            ordered=False,
        )

        assert len(Request.objects.filter(command_type="ACTION")) == 1
        assert len(Request.objects.filter(expiration_at=None)) == 1

        find_missing_expiration_requests()
        prune_requests()

        assert len(Request.objects.filter(command_type="ACTION")) == 0

    def test_skip_expiration_updater(self, clean_request):
        config._CONFIG = {
            "db": {"prune": {"batch_size": -1, "interval": 1, "ttl": {"action": 1}}}
        }

        parent = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="T",
            created_at=datetime.datetime.now(timezone.utc) + timedelta(minutes=60),
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
            created_at=datetime.datetime.now(timezone.utc) + timedelta(minutes=60),
            status="SUCCESS",
            command_type="ACTION",
            has_parent=True,
            parent=parent,
        )

        child.save()
        # Resave parent so the child gets set
        parent.save()

        assert (
            len(Request.objects.filter(command_type="ACTION", expiration_at__ne=None))
            == 2
        )

        find_missing_expiration_requests()
        prune_requests()
        assert (
            len(Request.objects.filter(command_type="ACTION", expiration_at__ne=None))
            == 2
        )

    def test_temp_children_expiration_updated(self):
        config._CONFIG = {
            "db": {"prune": {"batch_size": -1, "interval": 1, "ttl": {"action": 1}}}
        }

        grandparent = Request(
            system="T",
            system_version="T",
            instance_name="T",
            namespace="T",
            command="G",
            created_at=datetime.datetime.now(timezone.utc) - timedelta(minutes=60),
            status="IN_PROGRESS",
            command_type="ACTION",
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
            command_type="TEMP",
            has_parent=True,
            parent=grandparent,
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
            command_type="ACTION",
            has_parent=True,
            parent=parent,
        )

        child.save()
        parent.save()

        # Parent and child should have expiration since parent is TEMP and completed
        assert len(Request.objects.filter(expiration_at__ne=None)) == 2

        # No missing expiration requests should be recomputed
        find_missing_expiration_requests()
        assert len(Request.objects.filter(expiration_at__ne=None)) == 2

        # Parent and child should be pruned
        prune_requests()
        assert len(Request.objects.filter(expiration_at__ne=None)) == 0

        # Grandparent on completion should have expiration set
        grandparent.status = "SUCCESS"
        grandparent.save()
        assert len(Request.objects.filter(expiration_at__ne=None)) == 1


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
        config._CONFIG = {
            "db": {"prune": {"batch_size": -1, "interval": 1, "ttl": {"file": 1}}}
        }
        assert len(File.objects.all()) == 2

        prune_files()
        assert len(File.objects.all()) == 1

    def test_orphan_job(self, orphan_job_file, deleted_job_file):
        config._CONFIG = {
            "db": {"prune": {"batch_size": -1, "interval": 1, "ttl": {"file": 1}}}
        }
        assert len(File.objects.all()) == 2

        prune_files()
        assert len(File.objects.all()) == 1
