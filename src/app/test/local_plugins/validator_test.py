# -*- coding: utf-8 -*-

from pathlib import Path

import pytest
from box import Box
from mock import Mock
from pytest_lazyfixture import lazy_fixture

import beer_garden.local_plugins.validator as validator
from beer_garden.errors import PluginValidationError


@pytest.fixture
def config():
    return Box({"NAME": "FOO", "VERSION": "1", "PLUGIN_ENTRY": "entry.py"})


@pytest.fixture
def config_file(tmp_path, config):
    serialized_config = [f"{key}='{value}'" for key, value in config.items()]

    config_file = tmp_path / "beer.conf"
    config_file.write_text("\n".join(serialized_config))


@pytest.fixture
def entry_point(tmp_path, config):
    (tmp_path / config["PLUGIN_ENTRY"]).touch()


@pytest.fixture
def bad_path():
    return Path("/path/to/nowhere")


class TestValidatePlugin(object):
    def test_success(self, tmp_path, config_file, entry_point):
        assert validator.validate_plugin(tmp_path) is True

    @pytest.mark.parametrize("path", [None, lazy_fixture("bad_path")])
    def test_bad_path(self, path):
        assert validator.validate_plugin(path) is False

    def test_failure_missing_conf(self, tmp_path):
        # Not having the config_file fixture makes validation fail
        assert validator.validate_plugin(tmp_path) is False

    def test_failure_missing_entry(self, tmp_path, config_file):
        # Not having the entry_point fixture makes validation fail
        assert validator.validate_plugin(tmp_path) is False


class TestRequiredConfigKeys(object):
    def test_none_config(self):
        with pytest.raises(PluginValidationError):
            validator._required_keys(None)

    def test_missing_required_key(self):
        config_module = Mock(
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/entry.py",
            spec=["VERSION", "PLUGIN_ENTRY"],
        )

        with pytest.raises(PluginValidationError):
            validator._required_keys(config_module)

    def test_success(self):
        config_module = Mock(
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/entry.py",
            spec=["NAME", "VERSION", "PLUGIN_ENTRY"],
        )

        # No exception raised = success
        assert validator._required_keys(config_module) is None


class TestEntryPoint(object):
    def test_not_a_file(self, tmp_path, config):
        config.PLUGIN_ENTRY = "not_a_file"

        with pytest.raises(PluginValidationError):
            validator._entry_point(config, tmp_path)

    def test_good_file(self, tmp_path, config):
        (tmp_path / "entry.py").touch()

        config.PLUGIN_ENTRY = "entry.py"

        validator._entry_point(config, tmp_path)

    def test_good_package(self, tmp_path, config):
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()

        (plugin_dir / "__init__.py").touch()
        (plugin_dir / "__main__.py").touch()

        config.PLUGIN_ENTRY = "-m plugin"

        validator._entry_point(config, tmp_path)


class TestInstances(object):
    def test_missing(self, config):
        assert validator._instances(config) is None

    def test_success(self, config):
        config.INSTANCES = ["i1"]
        assert validator._instances(config) is None

    def test_failure(self, config):
        config.INSTANCES = "not a list"
        with pytest.raises(PluginValidationError):
            validator._instances(config)


class TestArgs(object):
    @pytest.mark.parametrize(
        "instances,args",
        [(None, ["foo", "bar"]), (["foo"], {"foo": ["arg1"]}), (None, None)],
    )
    def test_success(self, config, instances, args):
        config.INSTANCES = instances
        config.PLUGIN_ARGS = args
        assert validator._args(config) is None

    @pytest.mark.parametrize(
        "instances,args",
        [(None, "THIS IS WRONG"), (["foo"], {"bar": ["arg1"]}), (["foo"], {})],
    )
    def test_failure(self, config, instances, args):
        config.INSTANCES = instances
        config.PLUGIN_ARGS = args
        with pytest.raises(PluginValidationError):
            validator._args(config)


class TestIndividualArgs(object):
    @pytest.mark.parametrize("args", [None, ["good"]])
    def test_success(self, args):
        assert validator._individual_args(args) is None

    @pytest.mark.parametrize("args", ["string", [{"foo": "bar"}]])
    def test_failure(self, args):
        with pytest.raises(PluginValidationError):
            validator._individual_args(args)


class TestEnvironment(object):
    def test_missing(self, config):
        assert validator._environment(config) is None

    def test_success(self, config):
        config.ENVIRONMENT = {"foo": "bar"}
        assert validator._environment(config) is None

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
            validator._environment(config)
