# -*- coding: utf-8 -*-
from datetime import timedelta

import pytest
from mock import MagicMock, Mock, patch

from beer_garden.db.mongo.models import File, RawFile, Request
from beer_garden.db.mongo.pruner import MongoPruner


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
    return MongoPruner(tasks=[task])


class TestMongoPruner(object):
    @patch("beer_garden.db.mongo.pruner.Q", MagicMock())
    def test_prune_something(self, pruner, collection_mock):
        pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))

        pruner.run()
        assert collection_mock.objects.return_value.no_cache.return_value.delete.called


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
