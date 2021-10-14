import logging
import pathlib
import tempfile
import textwrap
from pathlib import Path

import pytest
from box import Box
from brewtils.models import Instance, System
from mock import Mock
from pytest_lazyfixture import lazy_fixture

import beer_garden.db.api as db
from beer_garden.errors import PluginValidationError
from beer_garden.local_plugins.manager import CONFIG_NAME, ConfigLoader, PluginManager
from beer_garden.systems import create_system


@pytest.fixture
def config_all():
    return {
        "NAME": "foo",
        "VERSION": "1.0",
        "PLUGIN_ENTRY": "entry.py",
        "DESCRIPTION": "",
        "INSTANCES": ["default"],
        "PLUGIN_ARGS": {"default": None},
        "METADATA": {},
        "ENVIRONMENT": {},
        "ICON_NAME": None,
        "DISPLAY_NAME": None,
        "LOG_LEVEL": "INFO",
        "MAX_INSTANCES": 1,
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
            MAX_INSTANCES=1
        """
    )


@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield pathlib.Path(tmp_dir)


@pytest.fixture
def plugin_1(tmp_path, config_all_serialized):
    plugin_1 = tmp_path / "plugin_1"
    plugin_1.mkdir()

    write_file(plugin_1, config_all_serialized)

    return plugin_1


@pytest.fixture
def manager(tmp_path):
    PluginManager._runners = {}
    return PluginManager(
        plugin_dir=tmp_path,
        log_dir="plugin_logs",
        connection_info=Mock(),
        username="username",
        password="password",
    )


def write_file(plugin_path, file_contents):
    config_file = plugin_path / "beer.conf"
    config_file.write_text(file_contents)

    return config_file


def _none_returner(*args, **kwargs):
    return None


class TestHandlersAndRunnerMethods:
    @pytest.mark.parametrize(
        "method,method_args, exception",
        [
            ("get_runner", (None,), None),
            ("restart", (None, None), None),
            ("update", (None, None), None),
            ("stop_one", (None, None), Exception),
        ],
    )
    def test_runner_or_instance_ops_none_args(
        self, method, method_args, exception, manager
    ):
        """Test operations on runners/instances return `None` if given args of `None`"""
        if exception is not None:  # expect an exception
            with pytest.raises(exception):
                getattr(manager, method)(*method_args)
        else:
            assert getattr(manager, method)(*method_args) is None


@pytest.mark.skip
class TestLoadPlugins(object):
    def test_empty(self, tmp_path, loader):
        loader.load_plugins(path=tmp_path)

    def test_exception(self, monkeypatch, tmp_path, loader):
        monkeypatch.setattr(loader, "load_plugin", Mock(side_effect=ValueError()))

        # Just ensure that an exception during loading does NOT propagate out
        loader.load_plugins(path=tmp_path)


class TestLoadNew(object):
    def test_path_with_no_plugins(self, tmp_path, manager):
        manager.scan_path([tmp_path])
        assert manager._runners == []

    def test_single(self, tmp_path, manager, monkeypatch):
        monkeypatch.setattr(PluginManager, "_environment", _none_returner)

        plugin_path = tmp_path / "tester"
        plugin_path.mkdir()
        (plugin_path / "entry.py").touch()

        write_file(plugin_path, "PLUGIN_ENTRY='entry.py'")

        manager.scan_path([plugin_path])
        assert len(manager._runners) == 1

    def test_multiple(self, tmp_path, manager, monkeypatch):
        monkeypatch.setattr(PluginManager, "_environment", _none_returner)

        plugin_path = tmp_path / "tester"
        plugin_path.mkdir()
        (plugin_path / "entry.py").touch()

        write_file(
            plugin_path,
            textwrap.dedent(
                """
                PLUGIN_ENTRY='entry.py'
                INSTANCES=['a', 'b']
            """
            ),
        )

        manager.scan_path([plugin_path])
        assert len(manager._runners) == 2

    def test_dot_dir(self, tmp_path, manager, monkeypatch, caplog):
        monkeypatch.setattr(PluginManager, "_environment", _none_returner)

        plugin_path = tmp_path / ".please_ignore"
        plugin_path.mkdir()

        with caplog.at_level(logging.DEBUG):
            manager.scan_path([plugin_path])

        assert len(manager._runners) == 0
        assert "Ignoring hidden" in caplog.messages[0]

    def test_scan_path_no_paths(self, manager, caplog):
        setattr(manager, "_plugin_path", None)

        with caplog.at_level(logging.DEBUG):
            result = manager.scan_path()

        assert result == []
        assert "no path" in caplog.messages[0]


class TestLoadPlugin(object):
    @pytest.fixture
    def _file_path(self, tmp_path):
        new_file_path = tmp_path / "new_file"
        new_file_path.touch()
        return new_file_path

    @pytest.fixture
    def _hidden_path(self, tmp_path):
        hidden_directory_path = tmp_path / ".hidden_directory"
        hidden_directory_path.mkdir()
        return hidden_directory_path

    @pytest.fixture
    def _good_path(self, tmp_path):
        good_directory_path = tmp_path / "good_directory"
        good_directory_path.mkdir()
        return good_directory_path

    @pytest.fixture
    def _good_path_bad_config(self, tmp_path):
        good_directory_base_path = tmp_path / "good_directory"
        good_directory_base_path.mkdir()
        bad_config_file = good_directory_base_path / CONFIG_NAME
        bad_config_file.mkdir()
        return good_directory_base_path

    @pytest.mark.parametrize(
        "value,message",
        [
            (None, "malformed plugin path"),
            (Path("/not/a_real/directory"), "does not exist"),
            (lazy_fixture("_file_path"), "is not a directory"),
            (Path("."), "Cannot determine plugin path"),
            (lazy_fixture("_hidden_path"), "Ignoring hidden plugin path"),
            (lazy_fixture("_good_path"), "does not exist"),
            (lazy_fixture("_good_path_bad_config"), "is not a file"),
        ],
    )
    def test_plugin_path_validator_bad_paths(self, value, message, manager, caplog):
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.DEBUG):
            assert not manager._is_valid_plugin_path(value, None, logger)

        assert message in caplog.messages[0]

    @pytest.mark.skip
    @pytest.mark.parametrize("path", [None, Path("/not/real")])
    def test_bad_path(self, loader, path):
        with pytest.raises(PluginValidationError):
            loader.load_plugin(path)

    @pytest.mark.skip
    def test_single_instance(self, loader, registry, plugin_1):
        plugin_runners = loader.load_plugin(plugin_1)

        assert len(plugin_runners) == 1
        assert plugin_runners[0].name == "foo[default]-1.0"
        assert plugin_runners[0].entry_point == "entry.py"

    @pytest.mark.skip
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

        plugin_runners = loader.load_plugin(plugin)
        assert len(plugin_runners) == 2

        sorted_runners = sorted(plugin_runners, key=lambda x: x.name)
        assert sorted_runners[0].name == "foo[instance1]-1.0"
        assert sorted_runners[0].entry_point == "entry.py"
        assert sorted_runners[1].name == "foo[instance2]-1.0"
        assert sorted_runners[1].entry_point == "entry.py"

    @pytest.mark.skip
    def test_existing(self, loader, registry, plugin_1):
        system_id = "58542eb571afd47ead90face"
        instance_id = "58542eb571afd47ead90beef"
        create_system(
            System(
                id=system_id,
                name="foo",
                version="1.0",
                instances=[Instance(id=instance_id)],
            )
        )

        plugin_runners = loader.load_plugin(plugin_1)

        assert len(plugin_runners) == 1
        assert str(plugin_runners[0].system.id) == system_id
        assert str(plugin_runners[0].instance.id) == instance_id
        assert plugin_runners[0].name == "foo[default]-1.0"
        assert plugin_runners[0].entry_point == "entry.py"

    @pytest.mark.skip
    def test_existing_multiple(self, tmp_path, loader, registry, plugin_1, bg_instance):
        """This is mainly to test that Instance IDs are correct

        We save a system with 2 instances:
         - instance1, 58542eb571afd47ead90beef
         - instance2, 58542eb571afd47ead90beee

        Then we load a plugin that defines instances [instance2, instance3].

        Correct behavior is:
         - instance1 removed from the database
         - instance3 created in the database
         - instance2 remains in the database, and the ID remains the same
        """

        instance1 = Instance(name="instance1", id="58542eb571afd47ead90beef")
        instance2 = Instance(name="instance2", id="58542eb571afd47ead90beee")
        create_system(
            System(name="foo", version="1.0", instances=[instance1, instance2])
        )

        plugin = tmp_path / "plugin"
        plugin.mkdir()

        write_file(
            plugin,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=["instance2", "instance3"]
            """
            ),
        )

        plugin_runners = loader.load_plugin(plugin)
        assert len(plugin_runners) == 2

        assert db.query_unique(Instance, name="instance1") is None
        assert db.query_unique(Instance, name="instance3") is not None

        instance2_db = db.query_unique(Instance, name="instance2")
        assert instance2_db is not None
        assert instance2_db.id == instance2.id

    @pytest.mark.skip
    def test_bad_config(self, monkeypatch, caplog, tmp_path, loader, validator):
        monkeypatch.setattr(
            loader, "_load_config", Mock(side_effect=PluginValidationError)
        )

        with caplog.at_level(logging.ERROR):
            assert loader.load_plugin(tmp_path) == []

        assert len(caplog.records) == 1


class TestLoadConfig(object):
    @pytest.fixture(autouse=True)
    def entry_point(self, tmp_path):
        (tmp_path / "entry.py").touch()

    @pytest.mark.skip
    def test_failure_missing_conf_file(self, tmp_path, loader):
        with pytest.raises(PluginValidationError):
            ConfigLoader._load_config(tmp_path)

    @pytest.mark.skip
    def test_failure_directory_conf_file(self, tmp_path, loader):
        (tmp_path / CONFIG_NAME).mkdir()

        with pytest.raises(PluginValidationError):
            loader._load_config(tmp_path)

    def test_all_attributes(self, tmp_path, config_all, config_all_serialized):
        write_file(tmp_path, config_all_serialized)

        assert ConfigLoader.load(tmp_path / CONFIG_NAME) == config_all

    @pytest.mark.skip
    def test_required_attributes(self, tmp_path, config_all):
        write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
            """
            ),
        )

        assert ConfigLoader.load(tmp_path / CONFIG_NAME) == config_all

    def test_instances_no_plugin_args(self, tmp_path):
        write_file(
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

        loaded_config = ConfigLoader.load(tmp_path / CONFIG_NAME)
        assert loaded_config["INSTANCES"] == ["instance1", "instance2"]
        assert loaded_config["PLUGIN_ARGS"] == {"instance1": None, "instance2": None}
        assert loaded_config["MAX_INSTANCES"] == -1

    def test_plugin_args_list_no_instances(self, tmp_path):
        write_file(
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

        loaded_config = ConfigLoader.load(tmp_path / CONFIG_NAME)
        assert loaded_config["INSTANCES"] == ["default"]
        assert loaded_config["PLUGIN_ARGS"] == {"default": ["arg1"]}
        assert loaded_config["MAX_INSTANCES"] == -1

    def test_plugin_args_dict_no_instances(self, tmp_path):
        write_file(
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

        loaded_config = ConfigLoader.load(tmp_path / CONFIG_NAME)
        assert sorted(loaded_config["INSTANCES"]) == sorted(["foo", "bar"])
        assert loaded_config["PLUGIN_ARGS"] == {"foo": ["arg1"], "bar": ["arg2"]}
        assert loaded_config["MAX_INSTANCES"] == -1

    def test_instance_and_args_list(self, tmp_path):
        write_file(
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

        loaded_config = ConfigLoader.load(tmp_path / CONFIG_NAME)
        assert sorted(loaded_config["INSTANCES"]) == sorted(["foo", "bar"])
        assert loaded_config["PLUGIN_ARGS"] == {"foo": ["arg1"], "bar": ["arg1"]}
        assert loaded_config["MAX_INSTANCES"] == -1

    def test_explicit_max_instances(self, tmp_path):
        write_file(
            tmp_path,
            textwrap.dedent(
                """
                NAME='foo'
                VERSION='1.0'
                PLUGIN_ENTRY='entry.py'
                INSTANCES=["foo", "bar"]
                MAX_INSTANCES=-1
            """
            ),
        )

        loaded_config = ConfigLoader.load(tmp_path / CONFIG_NAME)
        assert sorted(loaded_config["INSTANCES"]) == sorted(["foo", "bar"])
        assert loaded_config["MAX_INSTANCES"] == -1

    def test_invalid_args(self, tmp_path):
        write_file(
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

        with pytest.raises(PluginValidationError):
            ConfigLoader.load(tmp_path / CONFIG_NAME)


class TestConfigValidation(object):
    @pytest.fixture
    def config(self):
        return Box({"NAME": "FOO", "VERSION": "1", "PLUGIN_ENTRY": "entry.py"})

    @pytest.fixture
    def config_file(self, tmp_path, config):
        serialized_config = [f"{key}='{value}'" for key, value in config.items()]

        config_file = tmp_path / "beer.conf"
        config_file.write_text("\n".join(serialized_config))

    @pytest.fixture
    def entry_point(self, tmp_path, config):
        (tmp_path / config["PLUGIN_ENTRY"]).touch()

    class TestValidateConfig(object):
        def test_success(self, tmp_path, config, entry_point):
            assert ConfigLoader._validate(config, tmp_path) is None

        def test_failure(self, tmp_path, config):
            # Not having the entry_point fixture makes this fail
            with pytest.raises(PluginValidationError):
                ConfigLoader._validate(config, tmp_path)

    class TestEntryPoint(object):
        def test_not_a_file(self, tmp_path, config):
            # Not having the entry_point fixture makes this fail
            with pytest.raises(PluginValidationError):
                ConfigLoader._entry_point(config, tmp_path)

        def test_good_file(self, tmp_path, config, entry_point):
            assert ConfigLoader._entry_point(config, tmp_path) is None

        def test_good_package(self, tmp_path, config):
            plugin_dir = tmp_path / "plugin"
            plugin_dir.mkdir()

            (plugin_dir / "__init__.py").touch()
            (plugin_dir / "__main__.py").touch()

            config.PLUGIN_ENTRY = "-m plugin"

            ConfigLoader._entry_point(config, tmp_path)

    class TestInstances(object):
        def test_missing(self, config):
            assert ConfigLoader._instances(config) is None

        def test_success(self, config):
            config.INSTANCES = ["i1"]
            assert ConfigLoader._instances(config) is None

        def test_failure(self, config):
            config.INSTANCES = "not a list"
            with pytest.raises(PluginValidationError):
                ConfigLoader._instances(config)

    class TestArgs(object):
        @pytest.mark.parametrize(
            "instances,args",
            [(None, ["foo", "bar"]), (["foo"], {"foo": ["arg1"]}), (None, None)],
        )
        def test_success(self, config, instances, args):
            config.INSTANCES = instances
            config.PLUGIN_ARGS = args
            assert ConfigLoader._args(config) is None

        @pytest.mark.parametrize(
            "instances,args",
            [(None, "THIS IS WRONG"), (["foo"], {"bar": ["arg1"]}), (["foo"], {})],
        )
        def test_failure(self, config, instances, args):
            config.INSTANCES = instances
            config.PLUGIN_ARGS = args
            with pytest.raises(PluginValidationError):
                ConfigLoader._args(config)

    class TestIndividualArgs(object):
        @pytest.mark.parametrize("args", [None, ["good"]])
        def test_success(self, args):
            assert ConfigLoader._individual_args(args) is None

        @pytest.mark.parametrize("args", ["string", [{"foo": "bar"}]])
        def test_failure(self, args):
            with pytest.raises(PluginValidationError):
                ConfigLoader._individual_args(args)

    class TestEnvironment(object):
        def test_missing(self, config):
            assert ConfigLoader._environment(config) is None

        def test_success(self, config):
            config.ENVIRONMENT = {"foo": "bar"}
            assert ConfigLoader._environment(config) is None

        @pytest.mark.parametrize(
            "env",
            [
                "notadict",
                {1: "int_key_not_allowed"},
                {"BG_foo": "that_key_is_not_allowed"},
                {"foos": ["foo1", "foo2"]},
            ],
        )
        def test_failure(self, config, env):
            config.ENVIRONMENT = env
            with pytest.raises(PluginValidationError):
                ConfigLoader._environment(config)
