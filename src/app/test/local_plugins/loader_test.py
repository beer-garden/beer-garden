import logging
import sys
import textwrap

import pytest
from mock import Mock

from beer_garden.bg_utils.mongo.models import System
from beer_garden.local_plugins.loader import LocalPluginLoader


@pytest.fixture
def config_all():
    return {
        "NAME": "foo",
        "VERSION": "1.0",
        "PLUGIN_ENTRY": "entry.py",
        "DESCRIPTION": "",
        "INSTANCES": ["default"],
        "PLUGIN_ARGS": {"default": None},
        "REQUIRES": [],
        "METADATA": {},
        "ENVIRONMENT": {},
        "ICON_NAME": None,
        "DISPLAY_NAME": None,
        "LOG_LEVEL": logging.INFO,
    }


@pytest.fixture
def config_all_serialized():
    return textwrap.dedent(
        """
            NAME='foo'
            VERSION='1.0'
            PLUGIN_ENTRY='entry.py'
            DESCRIPTION=''
            INSTANCES=['default']
            PLUGIN_ARGS={'default': None}
            REQUIRES=[]
            METADATA={}
            ENVIRONMENT={}
            ICON_NAME=None
            DISPLAY_NAME=None
            LOG_LEVEL='INFO'
        """
    )


@pytest.fixture
def plugin_1(tmp_path, config_all_serialized):
    plugin_1 = tmp_path / "plugin_1"
    plugin_1.mkdir()

    write_file(plugin_1, config_all_serialized)

    return plugin_1


def write_file(plugin_path, file_contents):
    config_file = plugin_path / "beer.conf"
    config_file.write_text(file_contents)

    return config_file


@pytest.fixture
def registry():
    reg = Mock()
    reg.get_all_plugins.return_value = []
    reg.get_unique_plugin_names.return_value = []
    return reg


@pytest.fixture
def validator():
    return Mock()


@pytest.fixture
def loader(registry, validator):
    return LocalPluginLoader(validator, registry)


class TestLoadPlugins(object):
    def test_empty(self, tmp_path, loader):
        loader.load_plugins(path=tmp_path)

    def test_exception(self, monkeypatch, tmp_path, loader):
        monkeypatch.setattr(loader, "load_plugin", Mock(side_effect=ValueError()))

        # Just ensure that an exception during loading does NOT propagate out
        loader.load_plugins(path=tmp_path)


class TestScanPluginPath(object):
    def test_empty_path(self, tmp_path, loader):
        assert loader.scan_plugin_path(path=tmp_path) == []

    def test_none_path(self, tmp_path, loader):
        assert loader.scan_plugin_path() == []

    def test_plugins(self, tmp_path, loader):
        plugin_1 = tmp_path / "plugin_1"
        plugin_2 = tmp_path / "plugin_2"

        plugin_1.mkdir()
        plugin_2.mkdir()

        assert loader.scan_plugin_path(path=tmp_path) == [str(plugin_1), str(plugin_2)]


class TestValidatePluginRequirements(object):
    def test_no_plugins(self, loader, registry):
        loader.validate_plugin_requirements()
        assert not registry.remove.called

    def test_no_requirements(self, loader, registry):
        registry.get_all_plugins.return_value = [
            Mock(requirements=[], plugin_name="foo"),
            Mock(requirements=[], plugin_name="bar"),
        ]

        loader.validate_plugin_requirements()
        assert not registry.remove.called

    def test_good_requirements(self, loader, registry):
        registry.get_all_plugins.return_value = [
            Mock(requirements=[], plugin_name="foo"),
            Mock(requirements=["foo"], plugin_name="bar"),
        ]
        registry.get_unique_plugin_names.return_value = ["foo", "bar"]

        loader.validate_plugin_requirements()
        assert not registry.remove.called

    def test_requirements_not_found(self, loader, registry):
        registry.get_all_plugins.return_value = [
            Mock(requirements=[], plugin_name="foo"),
            Mock(requirements=["NOT_FOUND"], plugin_name="bar", unique_name="bar"),
        ]
        registry.get_unique_plugin_names.return_value = ["foo", "bar"]

        loader.validate_plugin_requirements()
        registry.remove.assert_called_once_with("bar")


class TestLoadPlugin(object):
    @pytest.fixture(autouse=True)
    def drop_systems(self, mongo_conn):
        System.drop_collection()

    def test_new(self, loader, registry, plugin_1):
        plugin_runners = loader.load_plugin(str(plugin_1))

        assert len(plugin_runners) == 1
        assert plugin_runners[0].name == "foo[default]-1.0"
        assert plugin_runners[0].entry_point == "entry.py"

    def test_existing(self, loader, registry, plugin_1):
        system_id = "58542eb571afd47ead90face"
        System(id=system_id, name="foo", version="1.0").save()

        plugin_runners = loader.load_plugin(str(plugin_1))

        assert len(plugin_runners) == 1
        assert str(plugin_runners[0].system.id) == system_id
        assert plugin_runners[0].name == "foo[default]-1.0"
        assert plugin_runners[0].entry_point == "entry.py"

    def test_multiple_instances(self, tmp_path, loader):
        plugin = tmp_path / "plugin"
        plugin.mkdir()

        write_file(
            plugin,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=["instance1", "instance2"]
            """
            ),
        )

        plugin_runners = loader.load_plugin(str(plugin))
        assert len(plugin_runners) == 2

        sorted_runners = sorted(plugin_runners, key=lambda x: x.name)
        assert sorted_runners[0].name == "foo[instance1]-1.0"
        assert sorted_runners[0].entry_point == "entry.py"
        assert sorted_runners[1].name == "foo[instance2]-1.0"
        assert sorted_runners[1].entry_point == "entry.py"

    def test_invalid(self, loader, validator):
        validator.validate_plugin.return_value = False
        assert loader.load_plugin("/invalid/plugin") is False


class TestLoadPluginConfig(object):
    def test_all_attributes(self, tmp_path, loader, config_all, config_all_serialized):
        config_file = write_file(tmp_path, config_all_serialized)

        assert loader._load_plugin_config(str(config_file)) == config_all
        assert "BGPLUGINCONFIG" not in sys.modules

    def test_required_attributes(self, tmp_path, loader, config_all):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
            """
            ),
        )

        assert loader._load_plugin_config(str(config_file)) == config_all
        assert "BGPLUGINCONFIG" not in sys.modules

    def test_instances_no_plugin_args(self, tmp_path, loader):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=["instance1", "instance2"]
                PLUGIN_ARGS=None
            """
            ),
        )

        loaded_config = loader._load_plugin_config(str(config_file))

        assert loaded_config["INSTANCES"] == ["instance1", "instance2"]
        assert loaded_config["PLUGIN_ARGS"] == {"instance1": None, "instance2": None}
        assert "BGPLUGINCONFIG" not in sys.modules

    def test_plugin_args_list_no_instances(self, tmp_path, loader):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=None
                PLUGIN_ARGS=["arg1"]
            """
            ),
        )

        loaded_config = loader._load_plugin_config(str(config_file))

        assert loaded_config["INSTANCES"] == ["default"]
        assert loaded_config["PLUGIN_ARGS"] == {"default": ["arg1"]}
        assert "BGPLUGINCONFIG" not in sys.modules

    def test_plugin_args_dict_no_instances(self, tmp_path, loader):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=None
                PLUGIN_ARGS={"foo": ["arg1"], "bar": ["arg2"]}
            """
            ),
        )

        loaded_config = loader._load_plugin_config(str(config_file))

        assert sorted(loaded_config["INSTANCES"]) == sorted(["foo", "bar"])
        assert loaded_config["PLUGIN_ARGS"] == {"foo": ["arg1"], "bar": ["arg2"]}
        assert "BGPLUGINCONFIG" not in sys.modules

    def test_instance_and_args_list(self, tmp_path, loader):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=["foo", "bar"]
                PLUGIN_ARGS=["arg1"]
            """
            ),
        )

        loaded_config = loader._load_plugin_config(str(config_file))

        assert sorted(loaded_config["INSTANCES"]) == sorted(["foo", "bar"])
        assert loaded_config["PLUGIN_ARGS"] == {"foo": ["arg1"], "bar": ["arg1"]}
        assert "BGPLUGINCONFIG" not in sys.modules

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("DEBUG", logging.DEBUG),
            ("WARNING", logging.WARNING),
            ("INVALID", logging.INFO),
        ],
    )
    def test_log_level(self, tmp_path, loader, value, expected):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                f"""
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                LOG_LEVEL='{value}'
            """
            ),
        )

        loaded_config = loader._load_plugin_config(str(config_file))

        assert loaded_config["LOG_LEVEL"] == expected
        assert "BGPLUGINCONFIG" not in sys.modules

    @pytest.mark.xfail
    def test_invalid_args(self, tmp_path, loader):
        config_file = write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                PLUGIN_ARGS="invalid"
            """
            ),
        )

        with pytest.raises(ValueError):
            loader._load_plugin_config(str(config_file))

        assert "BGPLUGINCONFIG" not in sys.modules
