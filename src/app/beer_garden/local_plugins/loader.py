# -*- coding: utf-8 -*-
import logging
import sys
from imp import load_source
from os import listdir
from os.path import isfile, join, abspath
from typing import List

from brewtils.models import Instance, System

from beer_garden.db.api import query_unique
import beer_garden.config
from beer_garden.local_plugins.plugin_runner import LocalPluginRunner
from beer_garden.systems import create_system


class LocalPluginLoader(object):
    """Class that helps with loading local plugins"""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        validator,
        registry,
        local_plugin_dir=None,
        plugin_log_directory=None,
        username=None,
        password=None,
    ):
        self.validator = validator
        self.registry = registry

        self._local_plugin_dir = local_plugin_dir
        self._plugin_log_directory = plugin_log_directory
        self._username = username
        self._password = password

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

        self.validate_plugin_requirements()

    def scan_plugin_path(self, path: str = None) -> List[str]:
        """Find valid plugin directories in a given path.

        Note: This scan does not walk the directory tree - all plugins must be
        in the top level of the given path.

        Args:
            path: The path to scan for plugins. If none will default to the
            plugin path specified at initialization.

        Returns:
            Paths specifying plugins
        """
        path = path or self._local_plugin_dir

        if path is None:
            return []
        else:
            return [
                abspath(join(path, plugin))
                for plugin in listdir(path)
                if not isfile(join(path, plugin))
            ]

    def validate_plugin_requirements(self):
        """Validate requirements for each plugin can be satisfied"""
        plugin_list = self.registry.get_all_plugins()
        plugin_names = self.registry.get_unique_plugin_names()
        plugins_to_remove = []

        for plugin in plugin_list:
            for required_plugin in plugin.requirements:
                if required_plugin not in plugin_names:
                    self.logger.warning(
                        "Not loading plugin %s - plugin requirement %s is not "
                        "a known plugin.",
                        plugin.system.name,
                        required_plugin,
                    )
                    plugins_to_remove.append(plugin)

        for plugin in plugins_to_remove:
            self.registry.remove(plugin.unique_name)

    def load_plugin(self, plugin_path):
        """Loads a plugin given a path to a plugin directory.

        It will use the validator to validate the plugin before registering the
        plugin in the database as well as adding an entry to the plugin map.

        :param plugin_path: The path of the plugin to load
        :return: The loaded plugin
        """
        if not self.validator.validate_plugin(plugin_path):
            self.logger.warning(
                "Not loading plugin at %s because it was invalid.", plugin_path
            )
            return False

        plugin_config = self._load_plugin_config(join(plugin_path, "beer.conf"))

        config_name = plugin_config["NAME"]
        config_version = plugin_config["VERSION"]
        config_entry = plugin_config["PLUGIN_ENTRY"]
        config_instances = plugin_config["INSTANCES"]
        config_args = plugin_config["PLUGIN_ARGS"]

        plugin_id = None
        plugin_commands = []
        plugin_instances = [Instance(name=name) for name in config_instances]

        # If this system already exists we need to do some stuff
        plugin_system = query_unique(System, name=config_name, version=config_version)
        if plugin_system:
            # Carry these over to the new system
            plugin_id = plugin_system.id
            plugin_commands = plugin_system.commands

            for instance in plugin_instances:
                existing_instance = plugin_system.get_instance(instance.name)
                if existing_instance:
                    instance.id = existing_instance.id

            # TODO - Remove dangling instances
            # plugin_system.delete_instances()

        plugin_system = System(
            id=plugin_id,
            name=config_name,
            version=config_version,
            commands=plugin_commands,
            instances=plugin_instances,
            max_instances=len(plugin_instances),
            description=plugin_config.get("DESCRIPTION"),
            icon_name=plugin_config.get("ICON_NAME"),
            display_name=plugin_config.get("DISPLAY_NAME"),
            metadata=plugin_config.get("METADATA"),
        )

        plugin_system = create_system(plugin_system)

        plugin_list = []
        for instance in plugin_instances:
            # TODO - Local plugin runner shouldn't require HTTP entry point
            plugin = LocalPluginRunner(
                config_entry,
                plugin_system,
                instance.name,
                abspath(plugin_path),
                beer_garden.config.get("entry.http.host"),
                beer_garden.config.get("entry.http.port"),
                ssl_enabled=beer_garden.config.get("entry.http.ssl.enabled"),
                plugin_args=config_args.get(instance.name),
                environment=plugin_config["ENVIRONMENT"],
                requirements=plugin_config["REQUIRES"],
                plugin_log_directory=self._plugin_log_directory,
                url_prefix=beer_garden.config.get("entry.http.url_prefix"),
                ca_verify=False,
                ca_cert=beer_garden.config.get("entry.http.ssl.ca_cert"),
                username=self._username,
                password=self._password,
                log_level=plugin_config["LOG_LEVEL"],
            )

            self.registry.register_plugin(plugin)
            plugin_list.append(plugin)

        return plugin_list

    def _load_plugin_config(self, path_to_config):
        """Loads a validated plugin config"""
        self.logger.debug("Loading configuration at %s", path_to_config)

        config_module = load_source("BGPLUGINCONFIG", path_to_config)

        instances = getattr(config_module, "INSTANCES", None)
        plugin_args = getattr(config_module, "PLUGIN_ARGS", None)
        user_log_level = getattr(config_module, "LOG_LEVEL", "INFO")
        log_level = self._convert_log_level(user_log_level)

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
            "NAME": config_module.NAME,
            "VERSION": config_module.VERSION,
            "INSTANCES": instances,
            "PLUGIN_ENTRY": config_module.PLUGIN_ENTRY,
            "PLUGIN_ARGS": plugin_args,
            "DESCRIPTION": getattr(config_module, "DESCRIPTION", ""),
            "ICON_NAME": getattr(config_module, "ICON_NAME", None),
            "DISPLAY_NAME": getattr(config_module, "DISPLAY_NAME", None),
            "REQUIRES": getattr(config_module, "REQUIRES", []),
            "ENVIRONMENT": getattr(config_module, "ENVIRONMENT", {}),
            "METADATA": getattr(config_module, "METADATA", {}),
            "LOG_LEVEL": log_level,
        }

        if "BGPLUGINCONFIG" in sys.modules:
            del sys.modules["BGPLUGINCONFIG"]

        return config

    def _convert_log_level(self, level_name):
        try:
            return getattr(logging, str(level_name).upper())
        except AttributeError:
            return logging.INFO
