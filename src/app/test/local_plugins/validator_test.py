import sys

import pytest
from mock import Mock

from beer_garden.errors import PluginValidationError


@pytest.fixture
def config():
    return {"NAME": "FOO", "VERSION": "1", "PLUGIN_ENTRY": "entry.py"}


@pytest.fixture
def config_file(tmp_path, config):
    serialized_config = [f"{key}='{value}'" for key, value in config.items()]

    config_file = tmp_path / "beer.conf"
    config_file.write_text("\n".join(serialized_config))


@pytest.fixture
def entry_point(tmp_path, config):
    (tmp_path / config["PLUGIN_ENTRY"]).touch()


class TestValidatePlugin(object):
    @pytest.fixture(autouse=True)
    def remove_module(self):
        if "BGPLUGINCONFIG" in sys.modules:
            del sys.modules["BGPLUGINCONFIG"]

    def test_success(self, tmp_path, validator, config_file, entry_point):
        assert validator.validate_plugin(tmp_path) is True

        assert "BGPLUGINCONFIG" not in sys.modules

    def test_failure_missing_conf(self, tmp_path, validator):
        # Not having the config_file fixture makes validation fail
        assert validator.validate_plugin(tmp_path) is False

        assert "BGPLUGINCONFIG" not in sys.modules

    def test_failure_missing_entry(self, tmp_path, validator, config_file):
        # Not having the entry_point fixture makes validation fail
        assert validator.validate_plugin(tmp_path) is False

        assert "BGPLUGINCONFIG" not in sys.modules


class TestValidatePath(object):
    def test_success(self, tmpdir, validator):
        assert validator.validate_plugin_path(tmpdir) is True

    @pytest.mark.parametrize("path", [None, "/path/to/nowhere"])
    def test_failure(self, validator, path):
        with pytest.raises(PluginValidationError):
            validator.validate_plugin_path(path)

    @pytest.mark.parametrize("path_to_plugin", [None, "/path/to/nowhere"])
    def test_validate_config_failure(self, validator, path_to_plugin):
        with pytest.raises(PluginValidationError):
            validator.validate_plugin_config(path_to_plugin)


class TestRequiredConfigKeys(object):
    def test_none_config(self, validator):
        with pytest.raises(PluginValidationError):
            validator.validate_required_config_keys(None)

    def test_missing_required_key(self, validator):
        config_module = Mock(
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/entry.py",
            spec=["VERSION", "PLUGIN_ENTRY"],
        )

        with pytest.raises(PluginValidationError):
            validator.validate_required_config_keys(config_module)

    def test_success(self, validator):
        config_module = Mock(
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/entry.py",
            spec=["NAME", "VERSION", "PLUGIN_ENTRY"],
        )

        # No exception raised = success
        assert validator.validate_required_config_keys(config_module) is None


class TestEntryPoint(object):
    def test_none_config_module(self, validator):
        with pytest.raises(PluginValidationError):
            validator.validate_entry_point(None, "/path/to/nowhere")

    def test_none_path_to_plugin(self, validator):
        with pytest.raises(PluginValidationError):
            validator.validate_entry_point({}, None)

    def test_no_entry_point_key(self, validator):
        with pytest.raises(PluginValidationError):
            validator.validate_entry_point(Mock(spec=[]), "/path/to/nowhere")

    def test_not_a_file(self, validator):
        with pytest.raises(PluginValidationError):
            validator.validate_entry_point(
                Mock(spec=[validator.ENTRY_POINT_KEY], PLUGIN_ENTRY="not_a_file"),
                "/path/to/nowhere",
            )

    def test_good_file(self, tmp_path, validator):
        (tmp_path / "entry.py").touch()

        validator.validate_entry_point(
            Mock(spec=[validator.ENTRY_POINT_KEY], PLUGIN_ENTRY="entry.py"), tmp_path
        )

    def test_good_package(self, tmp_path, validator):
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()

        (plugin_dir / "__init__.py").touch()
        (plugin_dir / "__main__.py").touch()

        validator.validate_entry_point(Mock(PLUGIN_ENTRY="-m plugin"), tmp_path)


class TestInstancesAndArgs(object):
    @pytest.mark.parametrize(
        "instances,args",
        [(None, ["foo", "bar"]), (["foo"], {"foo": ["arg1"]}), (None, None)],
    )
    def test_success(self, validator, instances, args):
        config_module = Mock(INSTANCES=instances, PLUGIN_ARGS=args, spec=[])
        assert validator.validate_instances_and_args(config_module) is True

    @pytest.mark.parametrize(
        "instances,args",
        [
            ("THIS IS WRONG", None),
            (None, "THIS IS WRONG"),
            (["foo"], {"bar": ["arg1"]}),
            (["foo"], {}),
        ],
    )
    def test_failure(self, validator, instances, args):
        config_module = Mock(INSTANCES=instances, PLUGIN_ARGS=args)
        with pytest.raises(PluginValidationError):
            validator.validate_instances_and_args(config_module)

    def test_none_config_module(self, validator):
        with pytest.raises(PluginValidationError):
            validator.validate_instances_and_args(None)


class TestIndividualPluginArguments(object):
    @pytest.mark.parametrize("args", [None, ["good"]])
    def test_success(self, validator, args):
        assert validator.validate_individual_plugin_arguments(args) is True

    @pytest.mark.parametrize("args", ["string", [{"foo": "bar"}]])
    def test_failure(self, validator, args):
        with pytest.raises(PluginValidationError):
            validator.validate_individual_plugin_arguments(args)


class TestPluginEnvironment(object):
    @pytest.mark.parametrize(
        "args",
        [
            Mock(spec=[]),  # No environment
            Mock(ENVIRONMENT={"foo": "bar"}),  # Good environment
        ],
    )
    def test_success(self, validator, args):
        assert validator.validate_plugin_environment(args) is True

    @pytest.mark.parametrize(
        "args",
        [
            None,
            Mock(ENVIRONMENT="notadict"),
            Mock(ENVIRONMENT={1: "int_key_not_allowed"}),
            Mock(ENVIRONMENT={"BG_foo": "that_key_is_not_allowed"}),
            Mock(ENVIRONMENT={"foos": ["foo1", "foo2"]}),
        ],
    )
    def test_failure(self, validator, args):
        with pytest.raises(PluginValidationError):
            validator.validate_plugin_environment(args)
