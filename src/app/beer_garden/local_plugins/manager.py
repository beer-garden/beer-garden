# -*- coding: utf-8 -*-
import string
from concurrent.futures import ThreadPoolExecutor, wait
from concurrent.futures._base import Future
from enum import Enum

import json
import logging
import os
import sys
from brewtils.models import Event, System
from brewtils.specification import _SYSTEM_SPEC
from brewtils.stoppable_thread import StoppableThread
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from random import choice
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional

import beer_garden.config as config
from beer_garden.errors import PluginValidationError
from beer_garden.local_plugins.env_help import expand_string
from beer_garden.local_plugins.runner import ProcessRunner

# This is ... complicated. See the PluginManager docstring
lpm_proxy = None

CONFIG_NAME = "beer.conf"

logger = logging.getLogger(__name__)


class ConfigKeys(Enum):
    PLUGIN_ENTRY = 1
    INSTANCES = 2
    PLUGIN_ARGS = 3
    ENVIRONMENT = 4
    LOG_LEVEL = 5
    CAPTURE_STREAMS = 6

    NAME = 7
    VERSION = 8
    DESCRIPTION = 9
    MAX_INSTANCES = 10
    ICON_NAME = 11
    DISPLAY_NAME = 12
    METADATA = 13
    NAMESPACE = 14
    INTERPRETER_PATH = 15


class PluginManager(StoppableThread):
    """Manages creation and destruction of PluginRunners

    The instance of this class is intended to be created with a
    ``multiprocessing.managers.BaseManager``. This essentially means that it lives in
    its own process, and access to it is achieved using a proxy object. This proxy
    object is the module-scoped ``lpm_proxy``.

    We do this because we can use the proxy object in the main application process AND
    we can pass it to the entry point processes. The entry point processes can then use
    the proxy transparently.

    There are some catches, of course. One is performance, but I don't think it's
    significant enough to be a concern. The other is important enough to emphasize:

      HEY: RETURN TYPES FOR ALL PUBLIC METHODS OF THIS CLASS **MUST** BE PICKLEABLE!

    This proxy concept is pretty neat, but at some point the data does need to traverse
    a process boundary. All public (non-underscore) methods are exposed (able to be
    called by a client using the proxy). That means that anything returned from those
    methods must be pickleable to work.
    """

    def __init__(
        self,
        plugin_dir=None,
        log_dir=None,
        connection_info=None,
        username=None,
        password=None,
    ):
        super().__init__(logger=logging.getLogger(__name__), name="PluginManager")

        self._display_name = "Plugin Manager"
        self._runners: List[ProcessRunner] = []

        self._plugin_path = Path(plugin_dir) if plugin_dir else None
        self._log_dir = log_dir
        self._connection_info = connection_info
        self._username = username
        self._password = password

    def run(self):
        self.logger.debug(self._display_name + " is started")

        while not self.wait(1):
            self.monitor()

        self.logger.debug(self._display_name + " is stopped")

    def monitor(self):
        """Ensure that processes are still alive

        Iterate through all runners, restarting any processes that have stopped.

        This must be done inside of the PluginManager class because of the
        process.poll() check. That can only be done from within this class.
        """
        for runner in self._runners:
            if self.stopped():
                break

            if runner.process and runner.process.poll() is not None:
                if runner.restart:
                    self.logger.warning(f"Runner {runner} stopped, restarting")
                    self._restart(runner)
                elif not runner.stopped and not runner.dead:
                    self.logger.warning(f"Runner {runner} is dead, not restarting")
                    runner.dead = True

    def paths(self) -> List[str]:
        """All current runner paths"""
        return list({runner.process_cwd for runner in self._runners})

    def runner_state(self) -> List[Dict]:
        """Get a representation of current runners"""
        return [runner.state() for runner in self._runners]

    def has_instance_id(self, instance_id: str) -> bool:
        """Bool indicating if a given instance ID has an associated runner"""
        return self._from_instance_id(instance_id=instance_id) is not None

    def handle_initialize(self, event: Event) -> None:
        """Called whenever an INSTANCE_INITIALIZED occurs

        This associates the event instance with a specific runner.
        """
        runner_id = event.payload.metadata.get("runner_id")

        if runner_id:
            instance = event.payload

            self.logger.debug(f"Associating {runner_id} with {instance.id}")

            runner = self._from_runner_id(runner_id)
            runner.associate(instance=instance)
            runner.restart = True

    def handle_stopped(self, event: Event) -> None:
        """Called whenever an INSTANCE_STOPPED occurs

        If the event instance is associated with any runner that this PluginManager
        knows about then that runner will be marked as stopped and no longer monitored.
        """
        runner = self._from_instance_id(event.payload.id)

        if runner:
            runner.stopped = True
            runner.restart = False
            runner.dead = False

    def restart(self, instance_id: str) -> None:
        """Restart the runner for a particular Instance ID"""
        runner = self._from_instance_id(instance_id)

        if runner:
            self._restart(runner)

    def stop_one(self, runner_id=None, instance_id=None) -> None:
        """Stop the runner for a given runner or Instance ID

        The PluginManager has no ability to places messages on the message queue, so
        it is expected that a stop message will already have been sent to the plugin
        that's being asked to stop.

        This will wait for the runner to stop for plugin.local.timeout.shutdown seconds.
        If the runner is not stopped after that time its process will be killed with
        SIGKILL.
        """
        runner = self._from_runner_id(runner_id) or self._from_instance_id(instance_id)

        # This needs to be called after sending a stop request, so the plugin should
        # already be shutting down. So wait for it to stop...
        runner.join(config.get("plugin.local.timeout.shutdown"))

        # ...and then kill it if necessary
        if runner.is_alive():
            self.logger.warning(f"Runner {runner_id} still alive, about to SIGKILL")
            runner.kill()

        runner.stopped = True
        runner.restart = False
        runner.dead = False

    def stop_system(self, system: System) -> None:
        """Stop all runners associated with Instances of a given System"""
        runners = [self._from_instance_id(i.id) for i in system.instances]
        runners = [r for r in runners if r is not None]

        return self._stop_multiple(runners=runners)

    def stop_all(self) -> None:
        """Stop all known runners"""
        return self._stop_multiple(self._runners)

    def reload_system(self, system: System) -> None:
        """Reload all runners for a given System

        This method will invoke the normal stop operation on all runners associated with
        Instances of the System. So this should only be called after sending a stop
        request to those plugins, otherwise you're going to wait for the shutdown
        timeout and then terminate the runners.
        """
        self.logger.debug(f"Reloading system {system}")

        # Grab the directory where the system lives so we can create new runners later
        system_path = None
        for instance in system.instances:
            if self.has_instance_id(instance.id):
                system_path = self._from_instance_id(instance.id).process_cwd
                break

        if not system_path:
            raise Exception(f"Error while reloading {system}: unable to determine path")

        # Wait for all runners to stop and remove them from self._runners
        self.stop_system(system)

        # Create and start new runners using the path
        self._create_runners(system_path)

    def scan_path(self, path: str = None) -> None:
        """Scan a given directory for valid plugins

        Note: This scan does not walk the directory tree - all plugins must be
        in the top level of the given path.

        Args:
            path: The path to scan. If none will default to the plugin path specified at
                initialization.

        Returns:
            None
        """
        plugin_path = path or self._plugin_path

        new_runners = []
        for path in plugin_path.iterdir():
            try:
                if path.is_dir() and path not in self.paths():
                    new_runners += self._create_runners(path)
            except Exception as ex:
                self.logger.exception(f"Error loading plugin at {path}: {ex}")

    def _from_instance_id(self, instance_id: str) -> Optional[ProcessRunner]:
        for runner in self._runners:
            if runner.instance_id == instance_id:
                return runner
        return None

    def _from_runner_id(self, runner_id: str) -> Optional[ProcessRunner]:
        for runner in self._runners:
            if runner.runner_id == runner_id:
                return runner
        return None

    def _restart(self, runner: ProcessRunner) -> None:
        new_runner = ProcessRunner(
            runner_id=runner.runner_id,
            process_args=runner.process_args,
            process_cwd=runner.process_cwd,
            process_env=runner.process_env,
            capture_streams=runner.capture_streams,
        )

        self._runners.remove(runner)
        self._runners.append(new_runner)

        new_runner.start()

    def _stop_multiple(self, runners: Iterable[ProcessRunner] = None) -> None:
        # If not specified, default to all runners
        if runners is None:
            runners = self._runners

        # If empty, we're done
        if len(runners) < 1:
            return

        shutdown_pool = ThreadPoolExecutor(len(runners))
        stop_futures: List[Future] = []

        for runner in runners:
            stop_futures.append(
                shutdown_pool.submit(self.stop_one, runner_id=runner.runner_id)
            )

        wait(stop_futures)

        for runner in runners:
            self._runners.remove(runner)

    def _create_runners(self, plugin_path: Path) -> List[ProcessRunner]:
        """Create and start ProcessRunners for a particular directory

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

        for instance_name in plugin_config["INSTANCES"]:
            runner_id = "".join([choice(string.ascii_letters) for _ in range(10)])
            capture_streams = plugin_config.get("CAPTURE_STREAMS")
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
                    capture_streams=capture_streams,
                )
            )

        self._runners += new_runners

        for runner in new_runners:
            self.logger.debug(f"Starting runner {runner}")
            runner.start()

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
        plugin_path: Path,
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

        # Allowed host env vars
        for env_var in config.get("plugin.local.host_env_vars"):
            if env_var in env:
                logger.warning(
                    f"Skipping host environment variable {env_var} for runner at "
                    f"{plugin_path} as it's already set in the process environment"
                )
            else:
                env[env_var] = os.environ.get(env_var, default="")

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
