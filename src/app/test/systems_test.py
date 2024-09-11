# -*- coding: utf-8 -*-
import pytest
from brewtils.errors import ModelValidationError
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import System as BrewtilsSystem
from mongoengine import connect

from beer_garden import config
from beer_garden.db.mongo.models import System
from beer_garden.systems import create_system, get_systems, update_system


@pytest.fixture
def system():
    yield create_system(
        BrewtilsSystem(
            name="original",
            version="v0.0.1",
            namespace="beer_garden",
            commands=[BrewtilsCommand(name="original")],
        )
    )

    System.drop_collection()


@pytest.fixture
def system2():
    yield create_system(
        BrewtilsSystem(
            name="original",
            version="v0.0.2",
            namespace="beer_garden",
            commands=[BrewtilsCommand(name="original")],
        )
    )

    System.drop_collection()


class TestSystem:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def test_disallow_command_updates(self, system):
        """System commands should not be allowed to update if the
        allow_command_updates config is set to False
        """
        config._CONFIG = {"plugin": {"allow_command_updates": False}}

        with pytest.raises(ModelValidationError):
            update_system(
                system=system,
                new_commands=[BrewtilsCommand(name="changed_command")],
            )

    def test_allow_command_updates(self, system):
        """System commands should be allowed to update if the
        allow_command_updates config is set to True
        """
        config._CONFIG = {"plugin": {"allow_command_updates": True}}
        updated_system = update_system(
            system=system,
            new_commands=[BrewtilsCommand(name="changed_command")],
        )
        assert (
            updated_system.commands[0].name == "changed_command"
        ), "System command should be updated with the new command name"

    def test_get_systems(self, system, system2):
        systems = get_systems()

        assert len(systems) == 2

        system_1_found = False
        system_2_found = False
        for db_system in systems:
            if db_system.version == system.version:
                system_1_found = True
            elif db_system.version == system2.version:
                system_2_found = True

        assert system_1_found
        assert system_2_found

    def test_get_systems_filtered(self, system, system2):
        systems = get_systems(filter_latest=True)

        assert len(systems) == 1

        system_1_found = False
        system_2_found = False
        for db_system in systems:
            if db_system.version == system.version:
                system_1_found = True
            elif db_system.version == system2.version:
                system_2_found = True

        assert not system_1_found
        assert system_2_found
