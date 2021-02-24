# -*- coding: utf-8 -*-
import pytest
from datetime import timedelta
from mock import MagicMock, Mock, patch

from beer_garden.db.mongo.models import Request
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
        config = {"info": 5, "action": 10}

        prune_tasks, run_every = MongoPruner.determine_tasks(**config)

        assert len(prune_tasks) == 1
        assert run_every == 2.5

        expiration_task = prune_tasks[0]

        assert expiration_task["collection"] == Request

        assert expiration_task["field"] == "expiration_date"

        assert expiration_task["delete_after"] == timedelta(minutes=0)

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

        expiration_task = prune_tasks[0]

        assert expiration_task["collection"] == Request

        assert expiration_task["field"] == "expiration_date"

        assert expiration_task["delete_after"] == timedelta(minutes=0)
