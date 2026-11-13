# -*- coding: utf-8 -*-
import pytest
from brewtils.errors import ModelValidationError
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import System as BrewtilsSystem

from beer_garden import config
from beer_garden.db.mongo.models import Garden, System, Topic
from beer_garden.systems import (
    clean_command,
    clean_parameter,
    clean_system,
    create_system,
    determine_latest,
    get_systems,
    update_system,
)


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test to ensure a clean state."""
    yield Garden(name="default", connection_type="LOCAL").save()
    System.drop_collection()
    Topic.drop_collection()
    Garden.drop_collection()


@pytest.fixture
def system():
    yield create_system(
        BrewtilsSystem(
            name="original",
            version="v0.0.1",
            namespace="beer_garden",
            garden_name="default",
            local=True,
            commands=[BrewtilsCommand(name="original")],
        )
    )


@pytest.fixture
def system2():
    yield create_system(
        BrewtilsSystem(
            name="original",
            version="v0.0.2",
            namespace="beer_garden",
            garden_name="default",
            local=True,
            commands=[BrewtilsCommand(name="original")],
        )
    )


@pytest.fixture
def system3():
    yield create_system(
        BrewtilsSystem(
            name="original",
            version="v0.0.0.dev0",
            namespace="beer_garden",
            garden_name="default",
            local=True,
            commands=[BrewtilsCommand(name="original")],
            instances=[
                BrewtilsInstance(
                    name="instance1",
                    status="RUNNING",
                )
            ],
        )
    )


@pytest.fixture
def system4():
    yield create_system(
        BrewtilsSystem(
            name="original",
            version="v0.0.0.dev1",
            namespace="beer_garden",
            garden_name="default",
            local=True,
            commands=[BrewtilsCommand(name="original")],
            instances=[
                BrewtilsInstance(
                    name="instance2",
                    status="RUNNING",
                )
            ],
        )
    )


@pytest.fixture
def system5():
    yield create_system(
        BrewtilsSystem(
            name="default",
            version="v0.0.1",
            namespace="beer_garden",
            garden_name="default",
            local=True,
            commands=[BrewtilsCommand(name="default")],
            instances=[
                BrewtilsInstance(
                    name="instance1",
                    status="STOPPED",
                )
            ],
        )
    )

    System.drop_collection()


@pytest.fixture
def system6():
    yield create_system(
        BrewtilsSystem(
            name="default",
            version="2.0.1rc2-git",
            namespace="beer_garden",
            garden_name="default",
            local=True,
            commands=[BrewtilsCommand(name="default")],
            instances=[
                BrewtilsInstance(
                    name="instance1",
                    status="STOPPED",
                )
            ],
        )
    )

    System.drop_collection()


class TestSystem:

    def test_disallow_command_updates(self, system):
        """System commands should not be allowed to update if the
        allow_command_updates config is set to False
        """
        config._CONFIG = {"plugin": {"allow_command_updates": False}}

        with pytest.raises(ModelValidationError):
            update_system(
                system=system, new_commands=[BrewtilsCommand(name="changed_command")]
            )

    def test_allow_command_updates(self, system):
        """System commands should be allowed to update if the
        allow_command_updates config is set to True
        """
        config._CONFIG = {"plugin": {"allow_command_updates": True}}
        updated_system = update_system(
            system=system, new_commands=[BrewtilsCommand(name="changed_command")]
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

    def test_get_systems_running(self, system, system2, system3, system4):
        systems = get_systems(filter_running=True)

        assert len(systems) == 2
        system_1_found = False
        system_2_found = False
        system_3_found = False
        system_4_found = False
        for db_system in systems:
            if db_system.version == system.version:
                system_1_found = True
            elif db_system.version == system2.version:
                system_2_found = True
            elif db_system.version == system3.version:
                system_3_found = True
            elif db_system.version == system4.version:
                system_4_found = True

        assert not system_1_found
        assert not system_2_found
        assert system_3_found
        assert system_4_found

    def test_get_systems_running_and_filtered(
        self, system, system2, system3, system4, system5
    ):
        systems = get_systems(filter_latest=True, filter_running=True)

        assert len(systems) == 2
        system_1_found = False
        system_2_found = False
        system_3_found = False
        system_4_found = False
        system_5_found = False
        for db_system in systems:
            if db_system.name == system.name and db_system.version == system.version:
                system_1_found = True
            elif (
                db_system.name == system2.name and db_system.version == system2.version
            ):
                system_2_found = True
            elif (
                db_system.name == system3.name and db_system.version == system3.version
            ):
                system_3_found = True
            elif (
                db_system.name == system4.name and db_system.version == system4.version
            ):
                system_4_found = True
            elif (
                db_system.name == system5.name and db_system.version == system5.version
            ):
                system_5_found = True

        assert not system_1_found
        assert not system_2_found
        assert not system_3_found
        assert system_4_found
        assert system_5_found

    def test_get_systems_filtered_including_not_running(
        self, system, system2, system3, system4, system5
    ):
        systems = get_systems(filter_latest=True, filter_running=False)

        assert len(systems) == 2
        system_1_found = False
        system_2_found = False
        system_3_found = False
        system_4_found = False
        system_5_found = False
        for db_system in systems:
            if db_system.name == system.name and db_system.version == system.version:
                system_1_found = True
            elif (
                db_system.name == system2.name and db_system.version == system2.version
            ):
                system_2_found = True
            elif (
                db_system.name == system3.name and db_system.version == system3.version
            ):
                system_3_found = True
            elif (
                db_system.name == system4.name and db_system.version == system4.version
            ):
                system_4_found = True
            elif (
                db_system.name == system5.name and db_system.version == system5.version
            ):
                system_5_found = True

        assert not system_1_found
        assert system_2_found
        assert not system_3_found
        assert not system_4_found
        assert system_5_found

    def test_determine_latest(self, system, system2, system3, system4, system5):
        """Choose latest from multiple versions"""
        assert (
            determine_latest([system, system2, system3, system4, system5]).version
            == system2.version
        )

    def test_determine_latest_mixed(self, system, system6):
        """Choose parseable version over invalid version"""
        assert determine_latest([system, system6]).version == system.version

    def test_determine_latest_legacy(self, system6):
        """Choose invalid version if no other options"""
        assert determine_latest([system6]).version == system6.version

    def test_determine_latest_no_systems(self):
        """Return none if no matching systems"""
        assert determine_latest([]) is None

    def test_clean_system_fail_max_instances(self, system):
        system.max_instances = 1
        system.instances.append(BrewtilsInstance(name="default1", status="RUNNING"))
        system.instances.append(BrewtilsInstance(name="default2", status="RUNNING"))
        with pytest.raises(ModelValidationError):
            clean_system(system)

    def test_clean_system_fail_duplicate_instance_names(self, system):
        system.max_instances = 2
        system.instances.append(BrewtilsInstance(name="default", status="RUNNING"))
        system.instances.append(BrewtilsInstance(name="default", status="RUNNING"))
        with pytest.raises(ModelValidationError):
            clean_system(system)

    def test_clean_system_fail_invalid_instance_name(self, system):
        system.max_instances = 2
        system.instances.append(BrewtilsInstance(name="default", status="BAD"))
        with pytest.raises(ModelValidationError):
            clean_system(system)

    def test_clean_system_set_max_instances(self, system):
        system.max_instances = None
        system.instances.append(BrewtilsInstance(name="default", status="RUNNING"))
        clean_system(system)

        assert system.max_instances == -1

    def test_clean_system_set_garden_name(self, system):
        config._CONFIG = {"garden": {"name": "somegarden"}}
        system.garden_name = None
        system.instances.append(BrewtilsInstance(name="default", status="RUNNING"))
        clean_system(system)

        assert system.garden_name == "somegarden"

    def test_clean_system_set_local(self, system):
        config._CONFIG = {"garden": {"name": "somegarden"}}
        system.garden_name = "somegarden"
        system.local = False
        system.instances.append(BrewtilsInstance(name="default", status="RUNNING"))
        clean_system(system)

        assert system.local is True

    def test_clean_command_fail_name(self, bg_command):
        bg_command.name = None

        with pytest.raises(ModelValidationError):
            clean_command(bg_command)

    def test_clean_command_set_command_type(self, bg_command):
        bg_command.command_type = None
        clean_command(bg_command)

        assert bg_command.command_type == "ACTION"

    def test_clean_command_fail_command_type(self, bg_command):
        bg_command.command_type = "INVALID"

        with pytest.raises(ModelValidationError):
            clean_command(bg_command)

    def test_clean_command_set_output_type(self, bg_command):
        bg_command.output_type = None
        clean_command(bg_command)

        assert bg_command.output_type == "STRING"

    def test_clean_command_fail_output_type(self, bg_command):
        bg_command.output_type = "INVALID"

        with pytest.raises(ModelValidationError):
            clean_command(bg_command)

    def test_clean_command_fail_duplicate_parameters(self, bg_command):
        bg_command.parameters.append(bg_command.parameters[0])

        with pytest.raises(ModelValidationError):
            clean_command(bg_command)

    def test_clean_parameter_set_type(self, bg_parameter):
        bg_parameter.type = None
        clean_parameter(bg_parameter)

        assert bg_parameter.type == "Any"

    def test_clean_parameter_fail_non_nullable_optional(self, bg_parameter):
        bg_parameter.nullable = False
        bg_parameter.optional = True
        bg_parameter.default = None

        with pytest.raises(ModelValidationError):
            clean_parameter(bg_parameter)

    def test_clean_parameter_fail_form_input_type(self, bg_parameter):
        bg_parameter.form_input_type = "INVALID"

        with pytest.raises(ModelValidationError):
            clean_parameter(bg_parameter)

    def test_clean_parameter_set_display_name(self, bg_parameter):
        bg_parameter.display_name = None
        clean_parameter(bg_parameter)

        assert bg_parameter.display_name == bg_parameter.key

    def test_clean_parameter_choices_fail_static(self, bg_parameter, bg_choices):
        bg_choices.type = "static"
        bg_choices.value = "str"
        bg_parameter.choices = bg_choices

        with pytest.raises(ModelValidationError):
            clean_parameter(bg_parameter)

    def test_clean_parameter_choices_fail_url(self, bg_parameter, bg_choices):
        bg_choices.type = "url"
        bg_choices.value = {"key": "value"}
        bg_parameter.choices = bg_choices

        with pytest.raises(ModelValidationError):
            clean_parameter(bg_parameter)

    def test_clean_parameter_choices_fail_command(self, bg_parameter, bg_choices):
        bg_choices.type = "command"
        bg_choices.value = ["list"]
        bg_parameter.choices = bg_choices

        with pytest.raises(ModelValidationError):
            clean_parameter(bg_parameter)

    def test_clean_parameter_choices_fail_command_missing_field(
        self, bg_parameter, bg_choices
    ):
        bg_choices.type = "command"
        bg_choices.value = {
            "command": "command",
            "system": "system",
            "missing_version": "version",
        }
        bg_parameter.choices = bg_choices

        with pytest.raises(ModelValidationError):
            clean_parameter(bg_parameter)
