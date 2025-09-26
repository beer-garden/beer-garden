# -*- coding: utf-8 -*-

from mongoengine import connect

import beer_garden.db.mongo.models
from beer_garden import config
from beer_garden.db.mongo.models import Garden
from beer_garden.db.mongo.util import (  # ensure_roles,; ensure_users,
    ensure_local_garden,
)


class TestEnsureLocalGarden:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

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
