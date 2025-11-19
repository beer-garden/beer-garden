# -*- coding: utf-8 -*-

import mongomock
import datetime
from datetime import timedelta, timezone
from unittest.mock import patch

from mongoengine import connect

import beer_garden.db.mongo.models
from beer_garden import config
from beer_garden.db.mongo.models import Garden, Request
from beer_garden.db.mongo.util import (  # ensure_roles,; ensure_users,
    cancel_local_outstanding,
    ensure_local_garden,
)

FAKE_TIME = datetime.datetime.now(timezone.utc) + timedelta(minutes=60)


class TestCancelRequests:
    @classmethod
    def setup_class(cls):
        connect(
        "beer_garden",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient,
    )

    def teardown_method(self):
        beer_garden.db.mongo.models.Request.drop_collection()

    @patch("beer_garden.db.mongo.util.datetime")
    def test_no_canceled_requests(self, mock_datetime, request_dict):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {"db": {"prune": {"in_progress_request_expiration": 1}}}

        request_dict["status"] = "SUCCESS"
        request_dict["updated_at"] = FAKE_TIME - timedelta(minutes=2)
        request_dict["created_at"] = FAKE_TIME - timedelta(minutes=2)
        request_dict["status_updated_at"] = FAKE_TIME - timedelta(minutes=2)

        del request_dict["has_parent"]
        del request_dict["parent"]

        Request(**request_dict).save()
        cancel_local_outstanding()

        assert Request.objects(status="CANCELED").count() == 0
        assert Request.objects(status="SUCCESS").count() == 1

    @patch("beer_garden.db.mongo.util.datetime")
    def test_cancel_local_request(self, mock_datetime, request_dict):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {
            "garden": {"name": "target_garden"},
            "db": {"prune": {"in_progress_request_expiration": 1}},
        }

        request_dict["status"] = "IN_PROGRESS"
        request_dict["updated_at"] = FAKE_TIME - timedelta(minutes=2)
        request_dict["created_at"] = FAKE_TIME - timedelta(minutes=2)
        request_dict["status_updated_at"] = FAKE_TIME - timedelta(minutes=2)

        del request_dict["has_parent"]
        del request_dict["parent"]

        request_dict["target_garden"] = "target_garden"

        Request(**request_dict).save()

        assert Request.objects(status="IN_PROGRESS").count() == 1

        cancel_local_outstanding()

        assert Request.objects(status="CANCELED").count() == 1
        assert Request.objects(status="IN_PROGRESS").count() == 0

    @patch("beer_garden.db.mongo.util.datetime")
    def test_skip_non_local_request(self, mock_datetime, request_dict):
        mock_datetime.now.return_value = FAKE_TIME
        config._CONFIG = {
            "garden": {"name": "target_garden"},
            "db": {"prune": {"in_progress_request_expiration": 1}},
        }

        request_dict["status"] = "IN_PROGRESS"
        request_dict["updated_at"] = FAKE_TIME - timedelta(minutes=2)
        request_dict["created_at"] = FAKE_TIME - timedelta(minutes=2)
        request_dict["status_updated_at"] = FAKE_TIME - timedelta(minutes=2)

        del request_dict["has_parent"]
        del request_dict["parent"]

        request_dict["target_garden"] = "not_target_garden"

        Request(**request_dict).save()

        assert Request.objects(status="IN_PROGRESS").count() == 1

        cancel_local_outstanding()

        assert Request.objects(status="CANCELED").count() == 0
        assert Request.objects(status="IN_PROGRESS").count() == 1


class TestEnsureLocalGarden:
    @classmethod
    def setup_class(cls):
        connect(
            "beer_garden",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
        )

    def teardown_method(self):
        beer_garden.db.mongo.models.Garden.drop_collection()

    def test_ensure_local_garden_creates_new_garden_from_config(self, monkeypatch):
        """ensure_local_garden should create a Garden entry in the database with
        name derived from the "garden.name" config setting and a connection type of
        LOCAL"""

        config._CONFIG = {"garden": {"name": "parent"}, "parent": {"sync_interval": 1}}

        ensure_local_garden()
        garden = Garden.objects.get(connection_type="LOCAL")

        assert garden.name == config.get("garden.name")

    def test_ensure_local_garden_updates_garden_from_config(self, monkeypatch):
        """ensure_local_garden should update the name of an existing Garden entry in the
        database with a connection type of LOCAL"""
        config._CONFIG = {"garden": {"name": "parent"}, "parent": {"sync_interval": 1}}

        Garden(name="thisshouldchange", connection_type="LOCAL").save()
        ensure_local_garden()
        garden = Garden.objects.get(connection_type="LOCAL")

        assert garden.name == config.get("garden.name")
