# -*- coding: utf-8 -*-
import json
import logging
import random
import string
import sys
from enum import Enum
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import List

from brewtils.specification import _SYSTEM_SPEC

import beer_garden.config
from beer_garden.errors import PluginValidationError
from beer_garden.local_plugins.env_help import expand_string_with_environment_var
from beer_garden.local_plugins.plugin_runner import PluginRunner
from beer_garden.local_plugins.registry import LocalPluginRegistry

CONFIG_NAME = "beer.conf"


class ConfigKeys(Enum):
    PLUGIN_ENTRY = 1
    INSTANCES = 2
    PLUGIN_ARGS = 3
    ENVIRONMENT = 4
    LOG_LEVEL = 5

    NAME = 6
    VERSION = 7
    DESCRIPTION = 8
    MAX_INSTANCES = 9
    ICON_NAME = 10
    DISPLAY_NAME = 11
    METADATA = 12


class LocalPluginLoader(object):
    """Class that helps with loading local plugins"""

    logger = logging.getLogger(__name__)

    _instance = None

    def __init__(
        self,
        plugin_dir=None,
        log_dir=None,
        connection_info=None,
        username=None,
        password=None,
    ):
        self.registry = LocalPluginRegistry.instance()

        self._plugin_path = Path(plugin_dir) if plugin_dir else None
        self._log_dir = log_dir
        self._connection_info = connection_info
        self._username = username
        self._password = password

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls(
                plugin_dir=beer_garden.config.get("plugin.local.directory"),
                log_dir=beer_garden.config.get("plugin.local.log_directory"),
                connection_info=beer_garden.config.get("entry.http"),
                username=beer_garden.config.get("plugin.local.auth.username"),
                password=beer_garden.config.get("plugin.local.auth.password"),
            )
        return cls._instance

    def load_plugins(self, path: str = None) -> None:
        """Load all plugins

        After each has been loaded, it checks the requirements to ensure
        the plugin can be loaded correctly.

        Args:
            path: The path to scan for plugins. If none will default to the
            plugin path specified at initialization.
        """
        for plugin_path in self.scan_plugin_path(path=path):
            try:
                self.load_plugin(plugin_path)
            except Exception as ex:
                self.logger.exception(
                    "Exception while loading plugin %s: %s", plugin_path, ex
                )

    def scan_plugin_path(self, path: Path = None) -> List[Path]:
        """Find valid plugin directories in a given path.

        Note: This scan does not walk the directory tree - all plugins must be
        in the top level of the given path.

        Args:
            path: The path to scan for plugins. If none will default to the
                plugin path specified at initialization.

        Returns:
            Potential paths containing plugins
        """
        path = path or self._plugin_path

        if path is None:
            return []

        return [x for x in path.iterdir() if x.is_dir()]

    def load_plugin(self, plugin_path: Path) -> List[PluginRunner]:
        """Loads a plugin given a path to a plugin directory.

        It will use the validator to validate the plugin before registering the
        plugin in the database as well as adding an entry to the plugin map.

        Args:
            plugin_path: The path of the plugin

        Returns:
            A list of plugin runners

        """
        config_file = plugin_path / CONFIG_NAME

        if not plugin_path:
            raise PluginValidationError(f"Plugin path {plugin_path} does not exist")
        if not plugin_path.is_dir():
            raise PluginValidationError(f"Plugin path {plugin_path} is not a directory")
        if not config_file.exists():
            raise PluginValidationError(f"Config file {config_file} does not exist")
        if not config_file.is_file():
            raise PluginValidationError(f"Config file {config_file} is not a file")

        try:
            plugin_config = _load_config(config_file)
        except PluginValidationError as ex:
            self.logger.error(f"Error loading config for plugin at {plugin_path}: {ex}")
            return []

        plugin_list = []
        for instance_name in plugin_config["INSTANCES"]:

            process_args = self._generate_process_args(plugin_config, instance_name)

            process_env = self._generate_environment(
                instance_name, plugin_config, plugin_path
            )

            unique = "".join([random.choice(string.ascii_lowercase) for _ in range(10)])

            plugin = PluginRunner(
                unique_name=unique,
                process_args=process_args,
                process_cwd=plugin_path,
                process_env=process_env,
                plugin_log_directory=self._log_dir,
                log_level=plugin_config.get("LOG_LEVEL"),
            )

            self.registry.register_plugin(plugin)
            plugin_list.append(plugin)

        return plugin_list

    @staticmethod
    def _generate_process_args(plugin_config, instance_name):
        process_args = [sys.executable]

        if plugin_config.get("PLUGIN_ENTRY"):
            process_args += plugin_config["PLUGIN_ENTRY"].split(" ")
        elif plugin_config.get("NAME"):
            process_args += ["-m", plugin_config["NAME"]]
        else:
            raise PluginValidationError("Can't generate process args")

        plugin_args = plugin_config["PLUGIN_ARGS"].get(instance_name)
        if plugin_args:
            process_args += plugin_args

        return process_args

    def _generate_environment(self, instance_name, plugin_config, plugin_path):
        env = {}

        # System info comes from config file
        for key in _SYSTEM_SPEC:
            key = key.upper()

            if key in plugin_config:
                env["BG_" + key] = plugin_config.get(key)

        # Connection info comes from Beer-garden config
        env.update(
            {
                "BG_HOST": self._connection_info.host,
                "BG_PORT": self._connection_info.port,
                "BG_URL_PREFIX": self._connection_info.url_prefix,
                "BG_SSL_ENABLED": self._connection_info.ssl.enabled,
                "BG_CA_CERT": self._connection_info.ssl.ca_cert,
                "BG_CA_VERIFY": False,  # TODO - Fix this
            }
        )

        # The rest
        env.update(
            {
                "BG_INSTANCE_NAME": instance_name,
                "BG_PLUGIN_PATH": plugin_path.resolve(),
                "BG_USERNAME": self._username,
                "BG_PASSWORD": self._password,
            }
        )

        if "LOG_LEVEL" in plugin_config:
            env["BG_LOG_LEVEL"] = plugin_config["LOG_LEVEL"]

        # ENVIRONMENT from beer.conf
        for key, value in plugin_config.get("ENVIRONMENT", {}).items():
            env[key] = expand_string_with_environment_var(str(value), env)

        # Ensure values are all strings
        for key, value in env.items():
            env[key] = json.dumps(value) if isinstance(value, dict) else str(value)

        return env


def _load_config(config_file: Path) -> dict:
    """Loads a plugin config"""

    config_module = _config_from_beer_conf(config_file)

    # validator.validate_config(config_module, plugin_path)

    config = {}
    for key in ConfigKeys:
        if hasattr(config_module, key.name):
            config[key.name] = getattr(config_module, key.name)

    # Instances and arguments need some normalization
    config.update(
        _normalize_instance_args(config.get("INSTANCES"), config.get("PLUGIN_ARGS"))
    )

    return config


def _config_from_beer_conf(config_file: Path) -> ModuleType:
    """Load a beer.conf file as a Python module"""

    # Need to construct our own Loader here, the default doesn't work with .conf
    loader = SourceFileLoader("bg_plugin_config", str(config_file))
    spec = spec_from_file_location("bg_plugin_config", config_file, loader=loader)
    config_module = module_from_spec(spec)
    spec.loader.exec_module(config_module)

    return config_module


def _normalize_instance_args(instances, args):
    """Normalize the different ways instances and arguments can be specified"""
    if instances is None and args is None:
        instances = ["default"]
        args = {"default": None}

    elif args is None:
        args = {}
        for instance_name in instances:
            args[instance_name] = None

    elif instances is None:
        if isinstance(args, list):
            instances = ["default"]
            args = {"default": args}
        elif isinstance(args, dict):
            instances = list(args.keys())
        else:
            raise ValueError(f"PLUGIN_ARGS must be list or dict, found {type(args)}")

    elif isinstance(args, list):
        temp_args = {}
        for instance_name in instances:
            temp_args[instance_name] = args

        args = temp_args

    else:
        raise PluginValidationError("Invalid INSTANCES and PLUGIN_ARGS combination")

    return {"INSTANCES": instances, "PLUGIN_ARGS": args}
