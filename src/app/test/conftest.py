# -*- coding: utf-8 -*-
import brewtils.test
import pytest
from box import Box
from mongoengine import connect

import beer_garden
import beer_garden.config as config
import beer_garden.events

pytest_plugins = ["brewtils.test.fixtures"]


def pytest_configure():
    # This is so the comparison helpers in brewtils.text.comparison to work correctly
    brewtils.test._running_tests = True
    beer_garden._running_tests = True


def pytest_unconfigure():
    delattr(brewtils.test, "_running_tests")
    delattr(beer_garden, "_running_tests")


@pytest.fixture(autouse=True)
def noop_event_manager():
    """Set a noop event manager so the tests don't try to publish things"""

    class NoopManager:
        def put(self, *args, **kwargs):
            pass

    beer_garden.events.manager = NoopManager()


@pytest.fixture(autouse=True)
def global_conf():
    config.assign(Box(default_box=True), force=True)


@pytest.fixture()
def mongo_conn():
    connect("beer_garden", host="mongomock://localhost")


@pytest.fixture
def bad_id():
    """A bad mongo ID"""
    return "".join(["1" for _ in range(24)])


@pytest.fixture
def jobstore(mongo_conn):
    """A Beer Garden Job Store."""
    from beer_garden.db.mongo.jobstore import MongoJobStore

    js = MongoJobStore()
    yield js
    js.remove_all_jobs()
