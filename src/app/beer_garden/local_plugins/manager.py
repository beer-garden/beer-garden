# -*- coding: utf-8 -*-

import json
import logging
import string
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Lock

import sys
from enum import Enum
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path, PosixPath
from random import choice
from types import ModuleType
from typing import Any, Dict, List, Optional

from brewtils.models import Event, Events, System
from brewtils.specification import _SYSTEM_SPEC
from brewtils.stoppable_thread import StoppableThread

import beer_garden
import beer_garden.config as config
from beer_garden.errors import PluginValidationError
from beer_garden.local_plugins.env_help import expand_string
from beer_garden.local_plugins.runner import ProcessRunner

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
    NAMESPACE = 13
    INTERPRETER_PATH = 14


class PluginManager(StoppableThread):
    """Manages creation and destruction of PluginRunners"""

    logger = logging.getLogger(__name__)
    _instance = None

    runners: List[ProcessRunner] = []

    def __init__(
        self,
        plugin_dir=None,
        log_dir=None,
        connection_info=None,
        username=None,
        password=None,
    ):
        self.display_name = "Plugin Manager"

        self._plugin_path = Path(plugin_dir) if plugin_dir else None
        self._log_dir = log_dir
        self._connection_info = connection_info
        self._username = username
        self._password = password

        super().__init__(logger=self.logger, name="PluginManager")

    def run(self):
        self.logger.info(self.display_name + " is started")

        while not self.wait(1):
            self.monitor()

        self.logger.info(self.display_name + " is stopped")

    def monitor(self):
        """Ensure that processes are still alive

        Iterate through all runners, restarting any processes that have stopped.
        """
        for runner in self.runners:
            if self.stopped() or beer_garden.application.stopped():
                break

            if runner.process and runner.process.poll() is not None:
                if runner.restart:
                    self.logger.warning(f"Runner {runner} stopped, restarting")
                    self.restart(runner)
                elif not runner.stopped and not runner.dead:
                    self.logger.warning(f"Runner {runner} is dead, not restarting")
                    runner.dead = True

    @classmethod
    def current_paths(cls):
        return [runner.process_cwd for runner in cls.runners]

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls(
                plugin_dir=config.get("plugin.local.directory"),
                log_dir=config.get("plugin.local.log_directory"),
                connection_info=config.get("entry.http"),
                username=config.get("plugin.local.auth.username"),
                password=config.get("plugin.local.auth.password"),
            )
        return cls._instance

    @classmethod
    def handle_event(cls, event):
        # Only care about local garden
        if event.garden == config.get("garden.name"):
            if event.name == Events.INSTANCE_INITIALIZED.name:
                cls.handle_associate(event)
            elif event.name == Events.INSTANCE_STARTED.name:
                cls.handle_start(event)
            elif event.name == Events.INSTANCE_STOPPED.name:
                cls.handle_stop(event)
            elif event.name == Events.SYSTEM_REMOVED.name:
                cls.remove_system(event.payload)
            elif event.name == Events.SYSTEM_RELOAD_REQUESTED.name:
                cls.instance().reload_system(event.payload)
            elif event.name == Events.SYSTEM_RESCAN_REQUESTED.name:
                cls.instance().scan_path()

    @classmethod
    def handle_associate(cls, event):
        runner_id = event.payload.metadata.get("runner_id")

        if runner_id:
            instance = event.payload

            runner = cls.from_runner_id(runner_id)
            runner.associate(instance=instance)
            runner.restart = True

    @classmethod
    def handle_start(cls, event: Event):
        runner_id = cls.from_instance_id(event.payload.id)

        if runner_id in cls.runners:
            cls.restart(runner_id)

    @classmethod
    def handle_stop(cls, event: Event):
        runner = cls.from_instance_id(event.payload.id)

        if runner:
            runner.stopped = True
            runner.restart = False
            runner.dead = False

    @classmethod
    def remove_system(cls, system: System) -> List[ProcessRunner]:
        remove_runners = []
        for instance in system.instances:
            for runner in cls.runners:
                if instance.id == runner.instance_id:
                    remove_runners.append(runner)

        for runner in remove_runners:
            cls.remove(runner)

        return remove_runners

    def reload_system(self, system: System):
        removed_runners = self.remove_system(system)

        # All removed runners should have the same path, so just grab the first
        new_runners = self.create_runners(removed_runners[0].process_cwd)

        self.runners += new_runners

        # We need to start these immediately, otherwise the instance IDs won't be
        # associated with runner IDs
        for runner in new_runners:
            self.start_one(runner)

    @classmethod
    def from_instance_id(cls, instance_id: str) -> Optional[ProcessRunner]:
        for runner in cls.runners:
            if runner.instance_id == instance_id:
                return runner
        return None

    @classmethod
    def from_runner_id(cls, runner_id: str) -> Optional[ProcessRunner]:
        for runner in cls.runners:
            if runner.runner_id == runner_id:
                return runner
        return None

    @classmethod
    def start_all(cls):
        for runner in cls.runners:
            runner.start()

    @classmethod
    def stop_all(cls):

        shutdown_pool = ThreadPoolExecutor(
            1 if len(cls.runners) < 1 else len(cls.runners)
        )
        futures = []

        for runner in cls.runners:
            futures.append(
                shutdown_pool.submit(cls.stop_one, runner_id=runner.runner_id)
            )

        wait(futures)

    @classmethod
    def start_one(cls, runner: ProcessRunner) -> None:
        runner.start()

    @classmethod
    def stop_one(cls, runner_id=None, instance_id=None):
        runner = cls.from_runner_id(runner_id) or cls.from_instance_id(instance_id)

        # The process should already be exiting so just wait for it
        runner.join(config.get("plugin.local.timeout.shutdown"))

        if runner.is_alive():
            cls.logger.warning(f"Runner {runner_id} still alive, about to SIGKILL")
            runner.kill()

    @classmethod
    def remove(cls, runner: ProcessRunner):
        cls.runners.remove(runner)

    @classmethod
    def restart(cls, runner: ProcessRunner):
        new_runner = ProcessRunner(
            runner_id=runner.runner_id,
            process_args=runner.process_args,
            process_cwd=runner.process_cwd,
            process_env=runner.process_env,
        )

        cls.runners.remove(runner)
        cls.runners.append(new_runner)

        new_runner.start()

    def scan_path(self, path: str = None) -> List[ProcessRunner]:
        """Create and start ProcessRunners for valid plugins in a given directory

        Note: This scan does not walk the directory tree - all plugins must be
        in the top level of the given path.

        Args:
            path: The path to scan. If none will default to the plugin path specified at
                initialization.

        Returns:
            Newly loaded and started runner dictionary
        """
        plugin_path = path or self._plugin_path

        new_runners = []
        for path in plugin_path.iterdir():
            try:
                if path.is_dir() and path not in self.current_paths():
                    new_runners += self.create_runners(path)
            except Exception as ex:
                self.logger.exception(f"Error loading plugin at {path}: {ex}")

        self.runners += new_runners

        for runner in new_runners:
            self.start_one(runner)

        return new_runners

    def create_runners(self, plugin_path: Path) -> List[ProcessRunner]:
        """Creates ProcessRunners for a particular directory

        It will use the validator to validate the config.

        Args:
            plugin_path: The path of the plugin

        Returns:
            Newly created runner dictionary

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
            plugin_config = ConfigLoader.load(config_file)
        except PluginValidationError as ex:
            self.logger.error(f"Error loading config for plugin at {plugin_path}: {ex}")
            return []

        new_runners = []
        error_log_lock = Lock()

        for instance_name in plugin_config["INSTANCES"]:
            runner_id = "".join([choice(string.ascii_letters) for _ in range(10)])
            process_args = self._process_args(plugin_config, instance_name)
            process_env = self._environment(
                plugin_config, instance_name, plugin_path, runner_id
            )

            new_runners.append(
                ProcessRunner(
                    runner_id=runner_id,
                    process_args=process_args,
                    process_cwd=plugin_path,
                    process_env=process_env,
                    error_log_lock=error_log_lock,
                )
            )

        return new_runners

    @staticmethod
    def _process_args(plugin_config, instance_name):
        if plugin_config.get("INTERPRETER_PATH"):
            process_args = [plugin_config.get("INTERPRETER_PATH")]
        else:
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

    def _environment(
        self,
        plugin_config: Dict[str, Any],
        instance_name: str,
        plugin_path: PosixPath,
        runner_id: str,
    ) -> Dict[str, str]:
        env = {}

        # System info comes from config file
        for key in _SYSTEM_SPEC:
            key = key.upper()

            if key in plugin_config:
                env["BG_" + key] = plugin_config.get(key)

        env.update(
            {
                # Connection info comes from Beer-garden config
                "BG_HOST": self._connection_info.host,
                "BG_PORT": self._connection_info.port,
                "BG_URL_PREFIX": self._connection_info.url_prefix,
                "BG_SSL_ENABLED": self._connection_info.ssl.enabled,
                "BG_CA_CERT": self._connection_info.ssl.ca_cert,
                "BG_CA_VERIFY": False,  # TODO - Fix this
                # The rest
                "BG_INSTANCE_NAME": instance_name,
                "BG_RUNNER_ID": runner_id,
                "BG_PLUGIN_PATH": plugin_path.resolve(),
                "BG_USERNAME": self._username,
                "BG_PASSWORD": self._password,
            }
        )

        if "LOG_LEVEL" in plugin_config:
            env["BG_LOG_LEVEL"] = plugin_config["LOG_LEVEL"]

        # Ensure values are all strings
        for key, value in env.items():
            env[key] = json.dumps(value) if isinstance(value, dict) else str(value)

        # ENVIRONMENT from beer.conf
        for key, value in plugin_config.get("ENVIRONMENT", {}).items():
            env[key] = expand_string(str(value), env)

        return env


class ConfigLoader(object):
    @staticmethod
    def load(config_file: Path) -> dict:
        """Loads a plugin config"""

        config_module = ConfigLoader._config_from_beer_conf(config_file)

        ConfigLoader._validate(config_module, config_file.parent)

        config_dict = {}
        for key in ConfigKeys:
            if hasattr(config_module, key.name):
                config_dict[key.name] = getattr(config_module, key.name)

        # Need to apply some normalization
        config_dict.update(
            ConfigLoader._normalize(
                config_dict.get("INSTANCES"),
                config_dict.get("PLUGIN_ARGS"),
                config_dict.get("MAX_INSTANCES"),
            )
        )

        return config_dict

    @staticmethod
    def _config_from_beer_conf(config_file: Path) -> ModuleType:
        """Load a beer.conf file as a Python module"""

        # Need to construct our own Loader here, the default doesn't work with .conf
        loader = SourceFileLoader("bg_plugin_config", str(config_file))
        spec = spec_from_file_location("bg_plugin_config", config_file, loader=loader)
        config_module = module_from_spec(spec)
        spec.loader.exec_module(config_module)

        return config_module

    @staticmethod
    def _normalize(instances, args, max_instances):
        """Normalize the config

        Will reconcile the different ways instances and arguments can be specified as
        well as determine the correct MAX_INSTANCE value
        """

        if isinstance(instances, list) and isinstance(args, dict):
            # Fully specified, nothing to translate
            pass

        elif instances is None and args is None:
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
                raise ValueError(
                    f"PLUGIN_ARGS must be list or dict, found {type(args)}"
                )

        elif isinstance(args, list):
            temp_args = {}
            for instance_name in instances:
                temp_args[instance_name] = args

            args = temp_args

        else:
            raise PluginValidationError("Invalid INSTANCES and PLUGIN_ARGS combination")

        if max_instances is None:
            max_instances = -1

        return {
            "INSTANCES": instances,
            "PLUGIN_ARGS": args,
            "MAX_INSTANCES": max_instances,
        }

    @staticmethod
    def _validate(config_module: ModuleType, path: Path) -> None:
        """Validate a plugin directory is valid

        Args:
            config_module: Configuration module to validate
            path: Path to directory containing plugin

        Returns:
            None

        Raises:
            PluginValidationError: Validation was not successful

        """
        ConfigLoader._entry_point(config_module, path)
        ConfigLoader._instances(config_module)
        ConfigLoader._args(config_module)
        ConfigLoader._environment(config_module)

    @staticmethod
    def _entry_point(config_module, path: Path) -> None:
        """Validates a plugin's entry point.

        An entry point is considered valid if the config has an entry with key
        PLUGIN_ENTRY and the value is a path to either a file or the name of a runnable
        Python module.
        """
        entry_point = getattr(config_module, ConfigKeys.PLUGIN_ENTRY.name, None)

        if not entry_point:
            return

        if (path / entry_point).is_file():
            return

        entry_parts = entry_point.split(" ")
        pkg = entry_parts[1] if entry_parts[0] == "-m" else entry_parts[0]
        pkg_path = path / pkg

        if (
            pkg_path.is_dir()
            and (pkg_path / "__init__.py").is_file()
            and (pkg_path / "__main__.py").is_file()
        ):
            return

        raise PluginValidationError(
            f"{ConfigKeys.PLUGIN_ENTRY.name} '{entry_point}' must be a Python file or a "
            f"runnable package"
        )

    @staticmethod
    def _instances(config_module) -> None:
        instances = getattr(config_module, ConfigKeys.INSTANCES.name, None)

        if instances is not None and not isinstance(instances, list):
            raise PluginValidationError(
                f"Invalid {ConfigKeys.INSTANCES.name} entry '{instances}': if present it "
                f"must be a list"
            )

    @staticmethod
    def _args(config_module) -> None:
        args = getattr(config_module, ConfigKeys.PLUGIN_ARGS.name, None)

        if args is None:
            return

        if isinstance(args, list):
            ConfigLoader._individual_args(args)

        elif isinstance(args, dict):
            instances = getattr(config_module, ConfigKeys.INSTANCES.name, None)

            for instance_name, instance_args in args.items():
                if instances is not None and instance_name not in instances:
                    raise PluginValidationError(
                        f"{ConfigKeys.PLUGIN_ARGS.name} contains key '{instance_name}' "
                        f"but that instance is not in {ConfigKeys.INSTANCES.name}"
                    )

                ConfigLoader._individual_args(instance_args)

            if instances:
                for instance_name in instances:
                    if instance_name not in args.keys():
                        raise PluginValidationError(
                            f"{ConfigKeys.INSTANCES.name} contains '{instance_name}' "
                            f"but that instance is not in {ConfigKeys.PLUGIN_ARGS.name}"
                        )

        else:
            raise PluginValidationError(
                f"Invalid {ConfigKeys.PLUGIN_ARGS.name} '{args}': must be a list or dict"
            )

    @staticmethod
    def _individual_args(args) -> None:
        """Validates an individual PLUGIN_ARGS entry"""
        if args is None:
            return

        if not isinstance(args, list):
            raise PluginValidationError(
                f"Invalid {ConfigKeys.PLUGIN_ARGS.name} entry '{args}': must be a list"
            )

        for arg in args:
            if not isinstance(arg, str):
                raise PluginValidationError(
                    f"Invalid plugin argument '{arg}': must be a string"
                )

    @staticmethod
    def _environment(config_module) -> None:
        """Validates ENVIRONMENT if specified.

        ENVIRONMENT must be a dictionary of Strings to Strings. Otherwise it is invalid.
        """
        env = getattr(config_module, ConfigKeys.ENVIRONMENT.name, None)

        if env is None:
            return

        if not isinstance(env, dict):
            raise PluginValidationError(
                f"Invalid {ConfigKeys.ENVIRONMENT.name} entry '{env}': if present it must "
                f"be a dict"
            )

        for key, value in env.items():
            if not isinstance(key, str):
                raise PluginValidationError(
                    f"Invalid {ConfigKeys.ENVIRONMENT.name} key '{key}': must be a string"
                )

            if not isinstance(value, str):
                raise PluginValidationError(
                    f"Invalid {ConfigKeys.ENVIRONMENT.name} value '{value}': must be a string"
                )

            if key.startswith("BG_"):
                raise PluginValidationError(
                    f"Invalid {ConfigKeys.ENVIRONMENT.name} key '{key}': Can't specify an "
                    f"environment variable with a 'BG_' prefix as it can mess with "
                    f"internal Beer-garden machinery. Sorry about that :/"
                )
