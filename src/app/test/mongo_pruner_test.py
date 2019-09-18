# -*- coding: utf-8 -*-
from datetime import timedelta

import pytest
from mock import MagicMock, Mock, patch

from beer_garden.bg_utils.mongo.models import Request, Event
from beer_garden.mongo_pruner import MongoPruner


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
    @patch("beer_garden.mongo_pruner.Q", MagicMock())
    def test_prune_something(self, pruner, collection_mock):
        pruner._stop_event = Mock(wait=Mock(side_effect=[False, True]))

        pruner.run()
        assert collection_mock.objects.return_value.delete.called


class TestDetermineTasks(object):
    def test_determine_tasks(self):
        config = {"info": 5, "action": 10, "event": 15}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)

        assert len(prune_tasks) == 3
        assert run_every == 2.5

        info_task = prune_tasks[0]
        action_task = prune_tasks[1]
        event_task = prune_tasks[2]

        assert info_task["collection"] == Request
        assert action_task["collection"] == Request
        assert event_task["collection"] == Event

        assert info_task["field"] == "created_at"
        assert action_task["field"] == "created_at"
        assert event_task["field"] == "timestamp"

        assert info_task["delete_after"] == timedelta(minutes=5)
        assert action_task["delete_after"] == timedelta(minutes=10)
        assert event_task["delete_after"] == timedelta(minutes=15)

    def test_setup_pruning_tasks_empty(self):
        prune_tasks, run_every = MongoPruner.determine_tasks()
        assert prune_tasks == []
        assert run_every is None

    def test_setup_pruning_tasks_one(self):
        config = {"info": -1, "action": 1, "event": -1}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)
        assert len(prune_tasks) == 1
        assert run_every == 0.5

    def test_setup_pruning_tasks_mixed(self):
        config = {"info": 5, "action": -1, "event": 15}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)
        assert len(prune_tasks) == 2
        assert run_every == 2.5

        info_task = prune_tasks[0]
        event_task = prune_tasks[1]

        assert info_task["collection"] == Request
        assert event_task["collection"] == Event

        assert info_task["field"] == "created_at"
        assert event_task["field"] == "timestamp"

        assert info_task["delete_after"] == timedelta(minutes=5)
        assert event_task["delete_after"] == timedelta(minutes=15)
