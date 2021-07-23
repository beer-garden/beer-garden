# -*- coding: utf-8 -*-
import pytest
from mock import Mock
from mongoengine import connect
from brewtils.models import System, Command
from brewtils.errors import ModelValidationError

import beer_garden
import beer_garden.router
from beer_garden.systems import create_system, update_system


@pytest.fixture()
def mongo_conn():
    connect("beer_garden", host="mongomock://localhost")


def test_disallow_system_command_updates(mongo_conn, monkeypatch):
    system = System(
        name="original",
        version="v0.0.1",
        namespace="beer_garden",
        commands=[Command(name="original")],
    )
    create_system(system)
    monkeypatch.setattr(beer_garden.db.api, "modify", Mock())
    monkeypatch.setattr(beer_garden.router, "add_routing_system", Mock())
    try:
        update_system(system=system, new_commands=[Command(name="changed_command")])
        raise AssertionError()
    except ModelValidationError:
        pass


def test_allow_system_command_updates(mongo_conn, monkeypatch):
    system = System(
        name="test",
        version="v0.0.1",
        namespace="beer_garden",
        commands=[Command(name="original")],
    )

    create_system(system)
    monkeypatch.setattr(beer_garden.config, "get", lambda x: True)
    monkeypatch.setattr(beer_garden.db.api, "modify", Mock())
    monkeypatch.setattr(beer_garden.router, "add_routing_system", Mock())
    update_system(system=system, new_commands=[Command(name="changed_command")])
