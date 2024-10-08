# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta

import pytest
from mock import MagicMock, Mock
from mongomock.gridfs import enable_gridfs_integration

from beer_garden import config
from beer_garden.db.mongo.models import File, RawFile, Request
from beer_garden.db.mongo.pruner import (
    determine_tasks,
    prune_action_requests,
    prune_admin_requests,
    prune_files,
    prune_info_requests,
    prune_outstanding,
    prune_temp_requests,
)

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
    rawfile = RawFile().save()
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
    def test_prune_info_requests(self, info_request):
        config._CONFIG = {"db": {"ttl": {"info": 1, "batch_size": -1}}}
        prune_info_requests()
        assert len(Request.objects.filter(command_type="INFO")) == 0

    def test_prune_action_requests(self, action_request):
        config._CONFIG = {"db": {"ttl": {"action": 1, "batch_size": -1}}}
        prune_action_requests()
        assert len(Request.objects.filter(command_type="ACTION")) == 0

    def test_prune_action_request_no_command_type(self, in_progress, created, canceled):
        config._CONFIG = {"db": {"ttl": {"action": 1, "batch_size": -1}}}
        prune_action_requests()
        assert len(Request.objects.filter(command_type="ACTION")) == 0
        assert len(Request.objects.filter(command_type=None)) == 2

    def test_prune_admin_requests(self, admin_request):
        config._CONFIG = {"db": {"ttl": {"admin": 1, "batch_size": -1}}}
        prune_admin_requests()
        assert len(Request.objects.filter(command_type="ADMIN")) == 0

    def test_prune_temp_requests(self, temp_request):
        config._CONFIG = {"db": {"ttl": {"temp": 1, "batch_size": -1}}}
        prune_temp_requests()
        assert len(Request.objects.filter(command_type="TEMP")) == 0

    def test_prune_files(self, file, raw_file):
        config._CONFIG = {"db": {"ttl": {"file": 1, "batch_size": -1}}}
        prune_files()
        assert len(File.objects.all()) == 0

    def test_run_cancels_outstanding_requests(self, task, in_progress, created):
        config._CONFIG = {"db": {"ttl": {"in_progress": 15}}}
        prune_outstanding()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "CANCELED"
        assert new_created.status == "CANCELED"

    def test_negative_cancel_threshold(self, task, in_progress, created):
        config._CONFIG = {"db": {"ttl": {"in_progress": -1}}}
        prune_outstanding()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "IN_PROGRESS"
        assert new_created.status == "CREATED"

    def test_none_cancel_threshold(self, task, in_progress, created):
        config._CONFIG = {"db": {"ttl": {}}}
        prune_outstanding()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "IN_PROGRESS"
        assert new_created.status == "CREATED"


class TestDetermineTasks(object):
    def test_determine_tasks(self):
        config = {"info": 5, "action": 10, "file": 15, "admin": 20}

        prune_tasks = determine_tasks(**config)

        assert len(prune_tasks) == 5

        info_task = prune_tasks[0]
        action_task = prune_tasks[1]
        admin_task = prune_tasks[2]
        file_task = prune_tasks[3]
        raw_file_task = prune_tasks[4]

        assert info_task["collection"] == Request
        assert action_task["collection"] == Request
        assert file_task["collection"] == File
        assert raw_file_task["collection"] == RawFile
        assert admin_task["collection"] == Request

        assert info_task["field"] == "created_at"
        assert action_task["field"] == "created_at"
        assert file_task["field"] == "updated_at"
        assert raw_file_task["field"] == "created_at"
        assert admin_task["field"] == "created_at"

        assert info_task["delete_after"] == timedelta(minutes=5)
        assert action_task["delete_after"] == timedelta(minutes=10)
        assert file_task["delete_after"] == timedelta(minutes=15)
        assert raw_file_task["delete_after"] == timedelta(minutes=15)
        assert admin_task["delete_after"] == timedelta(minutes=20)

    def test_setup_pruning_tasks_empty(self):
        prune_tasks = determine_tasks()
        assert prune_tasks == []

    def test_setup_pruning_tasks_one(self):
        config = {"info": -1, "action": 1}

        prune_tasks = determine_tasks(**config)
        assert len(prune_tasks) == 1

    def test_setup_pruning_tasks_mixed(self):
        config = {"info": 5, "action": -1}

        prune_tasks = determine_tasks(**config)
        assert len(prune_tasks) == 1

        info_task = prune_tasks[0]

        assert info_task["collection"] == Request

        assert info_task["field"] == "created_at"

        assert info_task["delete_after"] == timedelta(minutes=5)
