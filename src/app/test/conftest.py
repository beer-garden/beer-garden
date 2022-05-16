# -*- coding: utf-8 -*-
import brewtils.test
import pytest
from box import Box
from mongoengine import connect

import beer_garden
import beer_garden.config as config
import beer_garden.events
from beer_garden.db.mongo.models import (
    Event,
    File,
    Garden,
    Job,
    RawFile,
    RemoteRole,
    RemoteUser,
    Request,
    Role,
    System,
    User,
    UserToken,
)

pytest_plugins = ["brewtils.test.fixtures"]


@pytest.fixture(scope="module", autouse=True)
def mongo_conn():
    connect("beer_garden", host="mongomock://localhost")


@pytest.fixture(scope="module", autouse=True)
def data_cleanup():
    """Cleanup all data between test modules to ensure each one is independent"""
    yield
    Event.drop_collection()
    File.drop_collection()
    Garden.drop_collection()
    Job.drop_collection()
    RawFile.drop_collection()
    Request.drop_collection()
    RemoteRole.drop_collection()
    RemoteUser.drop_collection()
    Role.drop_collection()
    System.drop_collection()
    User.drop_collection()
    UserToken.drop_collection()


@pytest.fixture(scope="module")
def local_garden_name():
    return "somegarden"


@pytest.fixture(scope="module", autouse=True)
def app_config_auth_disabled(local_garden_name):
    app_config = Box(
        {
            "auth": {"enabled": False, "token_secret": "notsosecret"},
            "garden": {"name": local_garden_name},
        }
    )
    config.assign(app_config, force=True)
    yield app_config


@pytest.fixture
def app_config_auth_enabled(monkeypatch, local_garden_name):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "token_secret": "notsosecret",
                "authentication_handlers": {
                    "basic": {"enabled": True},
                },
            },
            "garden": {"name": local_garden_name},
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


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
