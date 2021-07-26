# -*- coding: utf-8 -*-
import pytest
from brewtils.errors import ModelValidationError
from brewtils.models import Command, System
from mongoengine import connect

from beer_garden import config
from beer_garden.systems import create_system, update_system


@pytest.fixture
def system():
    yield create_system(
        System(
            name="original",
            version="v0.0.1",
            namespace="beer_garden",
            commands=[Command(name="original")],
        )
    )


class TestSystem:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def test_disallow_system_command_updates(self, system):
        """System commands should not be allowed to update if the
        allow_system_command_updates config is set to False
        """
        config._CONFIG = {"plugin": {"allow_system_command_updates": False}}

        with pytest.raises(ModelValidationError):
            update_system(system=system, new_commands=[Command(name="changed_command")])

    def test_allow_system_command_updates(self, system):
        """System commands should be allowed to update if the
        allow_system_command_updates config is set to True
        """
        config._CONFIG = {"plugin": {"allow_system_command_updates": True}}
        updated_system = update_system(
            system=system, new_commands=[Command(name="changed_command")]
        )
        assert (
            updated_system.commands[0].name == "changed_command"
        ), "System command should be updated with the new command name"
