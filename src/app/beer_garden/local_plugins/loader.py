# -*- coding: utf-8 -*-
import logging
import random
import string

import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import List

import beer_garden.config
import beer_garden.local_plugins.validator as validator
from beer_garden.errors import PluginValidationError
from beer_garden.local_plugins.env_help import expand_string_with_environment_var
from beer_garden.local_plugins.plugin_runner import PluginRunner
from beer_garden.local_plugins.registry import LocalPluginRegistry
from beer_garden.local_plugins.validator import CONFIG_NAME


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
        if not plugin_path or not plugin_path.is_dir():
            raise PluginValidationError(f"Plugin path {plugin_path} is not a directory")

        try:
            plugin_config = self._load_config(plugin_path)
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
                log_level=plugin_config["LOG_LEVEL"],
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

    @staticmethod
    def _load_config(plugin_path: Path) -> dict:
        """Loads a plugin config"""
        config_file = plugin_path / CONFIG_NAME

        if not config_file.exists():
            raise PluginValidationError("Config file does not exist")

        if not config_file.is_file():
            raise PluginValidationError("Config file is not actually a file")

        # Need to construct our own Loader here, the default doesn't work with .conf
        loader = SourceFileLoader("bg_plugin_config", str(config_file))
        spec = spec_from_file_location("bg_plugin_config", config_file, loader=loader)
        config_module = module_from_spec(spec)
        spec.loader.exec_module(config_module)

        # validator.validate_config(config_module, plugin_path)

        instances = getattr(config_module, "INSTANCES", None)
        plugin_args = getattr(config_module, "PLUGIN_ARGS", None)

        if instances is None and plugin_args is None:
            instances = ["default"]
            plugin_args = {"default": None}

        elif plugin_args is None:
            plugin_args = {}
            for instance_name in instances:
                plugin_args[instance_name] = None

        elif instances is None:
            if isinstance(plugin_args, list):
                instances = ["default"]
                plugin_args = {"default": plugin_args}
            elif isinstance(plugin_args, dict):
                instances = list(plugin_args.keys())
            else:
                raise ValueError("Unknown plugin args type: %s" % plugin_args)

        elif isinstance(plugin_args, list):
            temp_args = {}
            for instance_name in instances:
                temp_args[instance_name] = plugin_args

            plugin_args = temp_args

        config = {
            "NAME": getattr(config_module, "NAME", None),
            "VERSION": getattr(config_module, "VERSION", None),
            "INSTANCES": instances,
            "PLUGIN_ARGS": plugin_args,
            "PLUGIN_ENTRY": getattr(config_module, "PLUGIN_ENTRY", None),
            "LOG_LEVEL": getattr(config_module, "LOG_LEVEL", "INFO"),
            "DESCRIPTION": getattr(config_module, "DESCRIPTION", ""),
            "ICON_NAME": getattr(config_module, "ICON_NAME", None),
            "DISPLAY_NAME": getattr(config_module, "DISPLAY_NAME", None),
            "REQUIRES": getattr(config_module, "REQUIRES", []),
            "ENVIRONMENT": getattr(config_module, "ENVIRONMENT", {}),
            "METADATA": getattr(config_module, "METADATA", {}),
        }

        return config

    def _generate_environment(self, instance_name, plugin_config, plugin_path):
        plugin_env = {
            "BG_NAME": plugin_config["NAME"],
            "BG_VERSION": plugin_config["VERSION"],
            "BG_INSTANCE_NAME": instance_name,
            "BG_PLUGIN_PATH": plugin_path.resolve(),
            "BG_LOG_LEVEL": plugin_config["LOG_LEVEL"],
            "BG_HOST": self._connection_info.host,
            "BG_PORT": self._connection_info.port,
            "BG_URL_PREFIX": self._connection_info.url_prefix,
            "BG_SSL_ENABLED": self._connection_info.ssl.enabled,
            "BG_CA_CERT": self._connection_info.ssl.ca_cert,
            "BG_CA_VERIFY": False,  # TODO - Fix this
            "BG_USERNAME": self._username,
            "BG_PASSWORD": self._password,
        }

        # Ensure values are all strings
        for key, value in plugin_env.items():
            plugin_env[key] = str(value)

        # Merge in the ENVIRONMENT from beer.conf
        for key, value in plugin_config["ENVIRONMENT"].items():
            plugin_env[key] = expand_string_with_environment_var(str(value), plugin_env)

        return plugin_env
