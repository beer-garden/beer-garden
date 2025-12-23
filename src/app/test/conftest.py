# -*- coding: utf-8 -*-
import os

import brewtils.test
import pytest
from box import Box
from mongoengine import Document, connect, disconnect_all
from mongoengine.connection import get_db
from testcontainers.mongodb import MongoDbContainer

import beer_garden
import beer_garden.config as config
import beer_garden.db.mongo.models
import beer_garden.events

pytest_plugins = ["brewtils.test.fixtures"]


@pytest.fixture(scope="session", autouse=True)
def mongo_conn():
    """A MongoDB connection for the duration of the test session."""
    mongo_version = os.getenv("MONGO_VERSION", "6.0")
    with MongoDbContainer(f"mongo:{mongo_version}") as mongo_container:
        connect(
            "beer_garden",
            host=mongo_container.get_connection_url(),
        )
        yield
        disconnect_all()


@pytest.fixture(scope="function", autouse=True)
def data_cleanup():
    """Cleanup all data between test modules to ensure each one is independent"""
    yield
    db = get_db()
    db.get_collection("fs.files").drop()
    db.get_collection("fs.chunks").drop()
    for model_name in beer_garden.db.mongo.models.__all__:
        mongo_class = getattr(beer_garden.db.mongo.models, model_name)
        if isinstance(mongo_class, Document):
            mongo_class.objects.delete()


@pytest.fixture(scope="module")
def local_garden_name():
    return "somegarden"


@pytest.fixture(scope="module", autouse=True)
def app_config_auth_disabled(local_garden_name):
    app_config = Box(
        {
            "auth": {
                "enabled": False,
                "token_secret": "notsosecret",
                "token_access_ttl": {
                    "garden_admin": 15,
                    "operator": 15,
                    "plugin_admin": 15,
                    "read_only": 15,
                },
                "token_refresh_ttl": {
                    "garden_admin": 720,
                    "operator": 720,
                    "plugin_admin": 720,
                    "read_only": 720,
                },
            },
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
                "token_access_ttl": {
                    "garden_admin": 15,
                    "operator": 15,
                    "plugin_admin": 15,
                    "read_only": 15,
                },
                "token_refresh_ttl": {
                    "garden_admin": 720,
                    "operator": 720,
                    "plugin_admin": 720,
                    "read_only": 720,
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
    del brewtils.test._running_tests
    del beer_garden._running_tests


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
