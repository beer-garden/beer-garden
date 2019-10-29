# -*- coding: utf-8 -*-
import pytest
from box import Box
from mock import Mock

import beer_garden.db.mongo.api
from pymongo.errors import ServerSelectionTimeoutError


class TestCheckConnection(object):
    @pytest.fixture
    def db_config(self):
        return Box(
            {
                "name": "db_name",
                "connection": {
                    "username": "db_username",
                    "password": "db_password",
                    "host": "db_host",
                    "port": "db_port",
                },
            }
        )

    def test_setup_database_connect(self, monkeypatch, db_config):
        connect_mock = Mock()
        monkeypatch.setattr(beer_garden.db.mongo.api, "connect", connect_mock)

        assert beer_garden.db.mongo.api.check_connection(db_config) is True
        connect_mock.assert_called_with(
            alias="aliveness",
            db="db_name",
            username="db_username",
            password="db_password",
            host="db_host",
            port="db_port",
            serverSelectionTimeoutMS=1000,
            socketTimeoutMS=1000,
        )

    def test_setup_database_connect_error(self, monkeypatch, db_config):
        connect_mock = Mock(side_effect=ServerSelectionTimeoutError())
        monkeypatch.setattr(beer_garden.db.mongo.api, "connect", connect_mock)

        assert beer_garden.db.mongo.api.check_connection(db_config) is False
