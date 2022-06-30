# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta

import pytest
from mock import MagicMock, Mock, patch
from mongomock.gridfs import enable_gridfs_integration

from beer_garden.db.mongo.models import File, RawFile, Request
from beer_garden.db.mongo.pruner import MongoPruner

enable_gridfs_integration()


@pytest.fixture
def collection_mock():
    return MagicMock(__name__="MOCK")


@pytest.fixture
def task(collection_mock):
    return {
        "collection": collection_mock,
        "field": "test",
        "delete_after": timedelta(microseconds=1),
        "additional_query": Mock(),
    }


@pytest.fixture
def pruner(task):
    return MongoPruner(tasks=[task], cancel_threshold=15)


@pytest.fixture
def negative_pruner(task):
    return MongoPruner(tasks=[task], cancel_threshold=-1)


@pytest.fixture
def none_pruner(task):
    return MongoPruner(tasks=[task], cancel_threshold=None)


@pytest.fixture
def in_progress():
    in_progress = Request(
        system="T",
        system_version="T",
        instance_name="T",
        namespace="T",
        command="T",
        created_at=datetime.datetime(2020, 5, 17),
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
        created_at=datetime.datetime(2020, 6, 17),
        status="CREATED",
    )
    created.save()
    yield created
    created.delete()


class TestMongoPruner(object):
    @patch("beer_garden.db.mongo.pruner.Q", MagicMock())
    def test_prune_something(self, pruner, collection_mock):
        pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))

        pruner.run()
        assert collection_mock.objects.return_value.no_cache.return_value.delete.called

    def test_run_cancels_outstanding_requests(self, pruner, in_progress, created):
        pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))
        pruner.run()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "CANCELED"
        assert new_created.status == "CANCELED"

    def test_negative_cancel_threshold(self, negative_pruner, in_progress, created):
        negative_pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))
        negative_pruner.run()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "IN_PROGRESS"
        assert new_created.status == "CREATED"

    def test_none_cancel_threshold(self, none_pruner, in_progress, created):
        none_pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))
        none_pruner.run()
        new_in_progress = Request.objects.get(id=in_progress.id)
        new_created = Request.objects.get(id=created.id)
        assert new_in_progress.status == "IN_PROGRESS"
        assert new_created.status == "CREATED"


class TestDetermineTasks(object):
    def test_determine_tasks(self):
        config = {"info": 5, "action": 10, "file": 15}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)

        assert len(prune_tasks) == 4
        assert run_every == 2.5

        info_task = prune_tasks[0]
        action_task = prune_tasks[1]
        file_task = prune_tasks[2]
        raw_file_task = prune_tasks[3]

        assert info_task["collection"] == Request
        assert action_task["collection"] == Request
        assert file_task["collection"] == File
        assert raw_file_task["collection"] == RawFile

        assert info_task["field"] == "created_at"
        assert action_task["field"] == "created_at"
        assert file_task["field"] == "updated_at"
        assert raw_file_task["field"] == "created_at"

        assert info_task["delete_after"] == timedelta(minutes=5)
        assert action_task["delete_after"] == timedelta(minutes=10)
        assert file_task["delete_after"] == timedelta(minutes=15)
        assert raw_file_task["delete_after"] == timedelta(minutes=15)

    def test_setup_pruning_tasks_empty(self):
        prune_tasks, run_every = MongoPruner.determine_tasks()
        assert prune_tasks == []
        assert run_every is None

    def test_setup_pruning_tasks_one(self):
        config = {"info": -1, "action": 1}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)
        assert len(prune_tasks) == 1
        assert run_every == 0.5

    def test_setup_pruning_tasks_mixed(self):
        config = {"info": 5, "action": -1}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)
        assert len(prune_tasks) == 1
        assert run_every == 2.5

        info_task = prune_tasks[0]

        assert info_task["collection"] == Request

        assert info_task["field"] == "created_at"

        assert info_task["delete_after"] == timedelta(minutes=5)
