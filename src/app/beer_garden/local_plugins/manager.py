# -*- coding: utf-8 -*-

import json
import logging
import string
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from random import choice
from types import ModuleType
from typing import Dict

import sys
from brewtils.models import Instance, Request
from brewtils.specification import _SYSTEM_SPEC
from brewtils.stoppable_thread import StoppableThread

import beer_garden
import beer_garden.config
import beer_garden.db.api as db
import beer_garden.local_plugins.validator as validator
import beer_garden.queue.api as queue
from beer_garden.errors import PluginValidationError
from beer_garden.instances import stop_instance
from beer_garden.local_plugins import ConfigKeys, CONFIG_NAME
from beer_garden.local_plugins.env_help import expand_string_with_environment_var
from beer_garden.local_plugins.plugin_runner import PluginRunner
from beer_garden.local_plugins.validator import validate_config


@dataclass
class Runner:
    instance: PluginRunner
    restart: bool = False
    dead: bool = False


class RunnerManager(StoppableThread):
    """Manages creation and destruction of PluginRunners"""

    logger = logging.getLogger(__name__)
    runners = {}

    _instance = None

    def __init__(
        self,
        plugin_dir=None,
        log_dir=None,
        connection_info=None,
        username=None,
        password=None,
    ):
        self.display_name = "Runner Manager"

        self._plugin_path = Path(plugin_dir) if plugin_dir else None
        self._log_dir = log_dir
        self._connection_info = connection_info
        self._username = username
        self._password = password

        super().__init__(logger=self.logger, name="RunnerManager")

    def run(self):
        self.logger.info(self.display_name + " is started")

        while not self.wait(1):
            self.monitor()

        self.logger.info(self.display_name + " is stopped")

    def monitor(self):
        """Make sure runners stay alive

        Iterate through all plugins, testing them one at a time.

        If any of them are dead restart them, otherwise just keep chugging along.
        """
        for runner_id, runner in self.runners.items():
            if self.stopped():
                break

            if runner.instance.process.poll() is not None:
                if runner.restart:
                    self.logger.warning(f"Runner {runner_id} stopped, restarting")
                    self.restart(runner_id)
                elif not runner.dead:
                    self.logger.warning(f"Runner {runner_id} is dead, not restarting")
                    runner.dead = True

    @classmethod
    def current_paths(cls):
        return [r.instance.process_cwd for r in cls.runners.values()]

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

    @classmethod
    def start_all(cls):
        for runner in cls.runners.values():
            runner.instance.start()

    @classmethod
    def stop_all(cls):
        """Attempt to stop all plugins."""
        from time import sleep
        sleep(1)

        for runner_id in cls.runners:
            cls.stop_one(runner_id)

    @classmethod
    def stop_one(cls, runner_id):
        runner = cls.runners[runner_id]

        if not runner.instance.is_alive():
            cls.logger.info(f"Runner {runner_id} was already stopped")
            return

        # try:
        #     cls.logger.info(f"About to stop runner {runner_id}")
        #     runner.terminate(timeout=3)
        # except subprocess.TimeoutExpired:
        #     cls.logger.error(f"Runner {runner_id} didn't terminate, about to kill")
        #     runner.kill()

    @classmethod
    def remove(cls, runner_id):
        del cls.runners[runner_id]

    @classmethod
    def restart(cls, runner_id):
        old_runner = cls.runners[runner_id]

        new_runner = PluginRunner(
            runner_id=old_runner.runner_id,
            process_args=old_runner.process_args,
            process_cwd=old_runner.process_cwd,
            process_env=old_runner.process_env,
        )

        cls.runners[runner_id] = new_runner

        new_runner.start()

    def load_new(self, path: str = None) -> None:
        """Create PluginRunners for all plugins in a directory

        Note: This scan does not walk the directory tree - all plugins must be
        in the top level of the given path.

        Args:
            path: The path to scan for plugins. If none will default to the
                plugin path specified at initialization.
        """
        plugin_path = path or self._plugin_path

        for path in plugin_path.iterdir():
            try:
                if path.is_dir() and path not in self.current_paths():
                    self.runners.update(self.create_runners(path))
            except Exception as ex:
                self.logger.exception(f"Error loading plugin at {path}: {ex}")

    def create_runners(self, plugin_path: Path) -> Dict[str, Runner]:
        """Creates PluginRunners for a particular plugin directory

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
            return {}

        new_runners = {}

        for instance_name in plugin_config["INSTANCES"]:
            runner_id = "".join([choice(string.ascii_letters) for _ in range(10)])
            process_args = self._process_args(plugin_config, instance_name)
            process_env = self._environment(
                plugin_config, instance_name, plugin_path, runner_id
            )

            new_runners[runner_id] = Runner(
                instance=PluginRunner(
                    runner_id=runner_id,
                    process_args=process_args,
                    process_cwd=plugin_path,
                    process_env=process_env,
                )
            )

        return new_runners

    @staticmethod
    def _process_args(plugin_config, instance_name):
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

    def _environment(self, plugin_config, instance_name, plugin_path, runner_id):
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
                "BG_RUNNER_ID": runner_id,
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

    validate_config(config_module, config_file.parent)

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


class LocalPluginsManager(object):
    """Manager that is capable of stopping/starting and restarting plugins"""

    def __init__(self, shutdown_timeout):
        self.logger = logging.getLogger(__name__)
        self.loader = LocalPluginLoader.instance()
        self.registry = LocalPluginRegistry.instance()
        self.shutdown_timeout = shutdown_timeout

    def start_plugin(self, plugin):
        """Start a specific plugin.

        If a plugin cannot be found (i.e. it was not loaded) then it will not do anything
        If the plugin is already running, it will do nothing.
        If a plugin instance has not started after the PLUGIN_STARTUP_TIMEOUT it will
        mark that instance as stopped

        :param plugin: The plugin to start
        :return: True if any plugin instances successfully started. False if the plugin
        does not exist or all instances failed to start
        """
        self.logger.info("Starting plugin %s", plugin.unique_name)

        plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
        plugin_status = plugin_instance.status

        if plugin_status in ["RUNNING", "STARTING"]:
            self.logger.info("Plugin %s is already running.", plugin.unique_name)
            return True

        if plugin_status == "INITIALIZING":
            new_plugin = plugin
        elif plugin_status in ["DEAD", "STOPPED"]:
            new_plugin = PluginRunner(
                plugin.entry_point,
                plugin.system,
                plugin.instance_name,
                plugin.path_to_plugin,
                plugin.web_host,
                plugin.web_port,
                ssl_enabled=plugin.ssl_enabled,
                plugin_args=plugin.plugin_args,
                environment=plugin.environment,
                requirements=plugin.requirements,
                plugin_log_directory=plugin.plugin_log_directory,
                url_prefix=plugin.url_prefix,
                ca_verify=plugin.ca_verify,
                ca_cert=plugin.ca_cert,
                username=plugin.username,
                password=plugin.password,
            )
            self.registry.remove(plugin.unique_name)
            self.registry.register_plugin(new_plugin)
        else:
            raise PluginStartupError("Plugin in an invalid state (%s)" % plugin_status)

        plugin_instance.status = "STARTING"
        db.update(plugin_instance)

        new_plugin.start()

        return True

    def stop_plugin(self, plugin):
        """Stops a Plugin

        :param plugin The plugin to stop.
        :return: None
        """
        self.logger.info("Stopping plugin %s", plugin.unique_name)

        plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
        plugin_status = plugin_instance.status

        # Need to mark the plugin as dead if it doesn't shut down cleanly
        clean_shutdown = True

        try:
            if plugin_status in ["DEAD", "STOPPED", "STOPPING"]:
                self.logger.info("Plugin %s was already stopped", plugin.unique_name)
                return
            elif plugin_status == "UNKNOWN":
                self.logger.warning(
                    "Couldn't determine status of plugin %s, "
                    "still attempting to stop",
                    plugin.unique_name,
                )
            else:
                plugin_instance.status = "STOPPING"
                db.update(plugin_instance)

            # Plugin must be marked as stopped before sending shutdown message
            plugin.stop()

            stop_instance(plugin_instance.id)

            # Now just wait for the plugin thread to die
            self.logger.info("Waiting for plugin %s to stop...", plugin.unique_name)
            plugin.join(self.shutdown_timeout)

        except Exception as ex:
            clean_shutdown = False
            self.logger.error(
                "Plugin %s raised exception while shutting down:", plugin.unique_name
            )
            self.logger.exception(ex)

        finally:
            if plugin.is_alive():
                self.logger.error(
                    "Plugin %s didn't terminate, about to kill", plugin.unique_name
                )
                plugin.kill()
                clean_shutdown = False

        # Local plugins will set their status to STOPPED in their stop handler
        if not clean_shutdown:
            self.logger.warning(
                "Plugin %s did not shutdown cleanly, " "marking as DEAD",
                plugin.unique_name,
            )
            plugin_instance.status = "DEAD"
            db.update(plugin_instance)

    def restart_plugin(self, plugin):
        self.stop_plugin(plugin)
        self.start_plugin(plugin)

    def reload_system(self, system_name, system_version):
        """Reload a specific system

        :param system_name: The name of the system to reload
        :param system_version: The version of the system to reload
        :return: None
        """
        plugins = self.registry.get_plugins_by_system(system_name, system_version)
        if len(plugins) < 1:
            message = "Could not reload system %s-%s: not found in the registry" % (
                system_name,
                system_version,
            )
            self.logger.error(message)
            raise Exception(message)  # TODO - Should not be raising Exception

        path_to_plugin = plugins[0].path_to_plugin

        # Verify the new configuration is valid before we remove the
        # current plugins from the registry
        if not validator.validate_plugin(path_to_plugin):
            message = (
                "Could not reload system %s-%s: new configuration is not valid"
                % (system_name, system_version)
            )
            self.logger.warning(message)
            raise Exception(message)

        for plugin in plugins:
            plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
            plugin_status = plugin_instance.status
            if plugin_status == "RUNNING":
                message = "Could not reload system %s-%s: running instances" % (
                    system_name,
                    system_version,
                )
                self.logger.warning(message)
                raise Exception(message)

        for plugin in plugins:
            self.registry.remove(plugin.unique_name)

        self.loader.load_plugin(path_to_plugin)

    def start_all_plugins(self):
        """Attempts to start all plugins"""
        self.logger.debug("Starting all plugins")

        for plugin in self.registry.get_all_plugins():
            self.start_plugin(plugin)

    def stop_all_plugins(self):
        """Attempt to stop all plugins."""
        self.logger.info("Stopping all plugins")

        for plugin in self.registry.get_all_plugins():
            try:
                self.stop_plugin(plugin)
            except Exception as ex:
                self.logger.error("Error stopping plugin %s", plugin.unique_name)
                self.logger.exception(ex)

    def scan_plugin_path(self):
        """Scans the default plugin directory for new plugins.

        Will also start any new plugins found.

        :return: None
        """
        scanned_plugins_paths = set(self.loader.scan_plugin_path())
        existing_plugin_paths = set(
            [plugin.path_to_plugin for plugin in self.registry.get_all_plugins()]
        )

        for plugin_path in scanned_plugins_paths.difference(existing_plugin_paths):
            try:
                loaded_plugins = self.loader.load_plugin(plugin_path)

                if not loaded_plugins:
                    raise Exception("Couldn't load plugin at %s" % plugin_path)

                for plugin in loaded_plugins:
                    self.start_plugin(plugin)
            except Exception as ex:
                self.logger.error(
                    "Error while attempting to load plugin at %s", plugin_path
                )
                self.logger.exception(ex)
