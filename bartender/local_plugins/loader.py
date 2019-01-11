import logging
import sys
from imp import load_source
from os import listdir
from os.path import isfile, join, abspath

import bartender
from bartender.local_plugins.plugin_runner import LocalPluginRunner
from bg_utils.mongo.models import Instance, System


class LocalPluginLoader(object):
    """Class that helps with loading local plugins"""

    logger = logging.getLogger(__name__)

    def __init__(self, validator, registry):
        self.validator = validator
        self.registry = registry

    def load_plugins(self):
        """Load all plugins

        After each has been loaded, it checks the requirements to ensure
        the plugin can be loaded correctly.
        """
        for plugin_path in self.scan_plugin_path():
            try:
                self.load_plugin(plugin_path)
            except Exception as ex:
                self.logger.exception(
                    "Exception while loading plugin %s: %s", plugin_path, ex
                )

        self.validate_plugin_requirements()

    def scan_plugin_path(self, path=None):
        """Find valid plugin directories in a given path.

        Note: This scan does not walk the directory tree - all plugins must be
        in the top level of the given path.

        :param path: The path to scan for plugins. If none will default to the
            plugin path specified at initialization.

        :return: A list containing paths specifying plugins
        """
        path = path or bartender.config.plugin.local.directory

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

        config = self._load_plugin_config(join(plugin_path, "beer.conf"))

        plugin_name = config["NAME"]
        plugin_version = config["VERSION"]
        plugin_entry = config["PLUGIN_ENTRY"]
        plugin_instances = config["INSTANCES"]
        plugin_args = config["PLUGIN_ARGS"]

        # If this system already exists we need to do some stuff
        plugin_id = None
        plugin_commands = []
        # TODO: replace this with a call from the EasyClient
        # plugin_system = self.easy_client.find_unique_system(
        #     name=plugin_name, version=plugin_version)
        plugin_system = System.find_unique(plugin_name, plugin_version)

        if plugin_system:
            # Remove the current instances so they aren't left dangling
            # TODO: This should be replaced with a network call
            plugin_system.delete_instances()

            # Carry these over to the new system
            plugin_id = plugin_system.id
            plugin_commands = plugin_system.commands

        plugin_system = System(
            id=plugin_id,
            name=plugin_name,
            version=plugin_version,
            commands=plugin_commands,
            instances=[
                Instance(name=instance_name) for instance_name in plugin_instances
            ],
            max_instances=len(plugin_instances),
            description=config.get("DESCRIPTION"),
            icon_name=config.get("ICON_NAME"),
            display_name=config.get("DISPLAY_NAME"),
            metadata=config.get("METADATA"),
        )

        # TODO: Right now, we have to save this system because the LocalPluginRunner
        # uses the database to determine status, specifically, it calls reload on the
        # instance object which we need to change to satisfy
        plugin_system.deep_save()

        plugin_list = []
        plugin_log_directory = bartender.config.plugin.local.log_directory
        for instance_name in plugin_instances:
            plugin = LocalPluginRunner(
                plugin_entry,
                plugin_system,
                instance_name,
                abspath(plugin_path),
                bartender.config.web.host,
                bartender.config.web.port,
                bartender.config.web.ssl_enabled,
                plugin_args=plugin_args.get(instance_name),
                environment=config["ENVIRONMENT"],
                requirements=config["REQUIRES"],
                plugin_log_directory=plugin_log_directory,
                url_prefix=bartender.config.web.url_prefix,
                ca_verify=bartender.config.web.ca_verify,
                ca_cert=bartender.config.web.ca_cert,
                username=bartender.config.plugin.local.auth.username,
                password=bartender.config.plugin.local.auth.password,
                log_level=config["LOG_LEVEL"],
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
