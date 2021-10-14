# -*- coding: utf-8 -*-
import json
import logging
import os
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait
from concurrent.futures._base import Future
from enum import Enum
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from random import choice
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional

from brewtils.models import Event, Events, Runner, System
from brewtils.specification import _SYSTEM_SPEC
from brewtils.stoppable_thread import StoppableThread

import beer_garden.config as config
from beer_garden.errors import PluginValidationError
from beer_garden.events import publish, publish_event
from beer_garden.local_plugins.env_help import expand_string
from beer_garden.local_plugins.runner import ProcessRunner

# This is ... complicated. See the PluginManager docstring
lpm_proxy = None  # type: Optional[PluginManager]

CONFIG_NAME = "beer.conf"

logger = logging.getLogger(__name__)


def runner(*args, **kwargs):
    return lpm_proxy.get_runner(*args, **kwargs)


def runners():
    return lpm_proxy.get_runners()


def update(*args, **kwargs):
    return lpm_proxy.update(*args, **kwargs)


def has_instance_id(*args, **kwargs):
    return lpm_proxy.has_instance_id(*args, **kwargs)


@publish_event(Events.RUNNER_STARTED)
def start(*args, **kwargs):
    return lpm_proxy.restart(*args, **kwargs)


@publish_event(Events.RUNNER_STOPPED)
def stop(*args, **kwargs):
    return lpm_proxy.stop_one(*args, **kwargs)


@publish_event(Events.RUNNER_REMOVED)
def remove(*args, **kwargs):
    kwargs.pop("remove", None)
    return stop(*args, remove=True, **kwargs)


def rescan(*args, **kwargs) -> List[Runner]:
    """Scan plugin directory and start any new runners.

    Args:
        *args: Arguments to pass to ``scan_path`` in the PluginManager object.
        **kwargs: Keyword arguments to pass to ``scan_path`` in the PluginManager
            object.

    Returns:
        A list of the new runners
    """
    new_runners = lpm_proxy.scan_path(*args, **kwargs)

    for the_runner in new_runners:
        publish(
            Event(
                name=Events.RUNNER_STARTED.name,
                payload_type=Runner.__name__,
                payload=the_runner,
            )
        )

    return new_runners


def reload(path: Optional[str] = None, system: Optional[System] = None):
    """Reload runners in a directory.

    Note:
        Will first remove any existing runners, stopping them if necessary, and then
        initiate a rescan on the directory.

    Args:
        path: The path to reload. It's expected this will be only the final part of the
            full path, so it will be appended to the overall plugin path. Optional.
        system: If path is not specified, will attempt to determine the correct path to
            use based on the given system.
    """
    all_runners = runners()

    if path is None:
        for instance in system.instances:
            for the_runner in all_runners:
                if the_runner.instance_id == instance.id:
                    path = the_runner.path
                    break

    logger.debug(f"Reloading runners in directory {path}")

    for the_runner in all_runners:
        if the_runner.path == path:
            remove(runner_id=the_runner.id, remove=True)

    return rescan(paths=[lpm_proxy.plugin_path() / path])


def handle_event(event: Event) -> None:
    """Delegate handling of events to the plugin manager.

    Deals only with instance events associated with the local garden.

    Args:
        event: An Event object we might be interested in.
    """
    if event.garden == config.get("garden.name"):
        if event.name == Events.INSTANCE_INITIALIZED.name:
            lpm_proxy.handle_initialize(event)
        elif event.name == Events.INSTANCE_STOPPED.name:
            lpm_proxy.handle_stopped(event)


class PluginManager(StoppableThread):
    """Manage creation and destruction of PluginRunners.

    The instance of this class is intended to be created with a
    ``multiprocessing.managers.BaseManager``. That is, it will exist in its own process
    and access is via a proxy object. This proxy object is the module-scoped
    ``lpm_proxy``.

    A proxied object is used so that it can be safely manipulated in the main
    application process and also safely passed to the entry point processes. The entry
    point processes can then use the proxy transparently.

    There are some catches: One is performance, but I don't think it's
    significant enough to be a concern. The other is important enough to emphasize:

      RETURN TYPES FOR ALL PUBLIC METHODS OF THIS CLASS **MUST** BE PICKLE-ABLE!

    At some point the data needs to traverse a process boundary. All public
    (non-underscored) methods are exposed and are therefore able to be called by a
    client using the proxy. That means that anything returned from those methods must be
    pickle-able to work.
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

        self._plugin_path: Optional[Path] = Path(plugin_dir) if plugin_dir else None
        self._log_dir: Optional[str] = log_dir
        self._connection_info = connection_info
        self._username: Optional[str] = username
        self._password: Optional[str] = password

        self._runner_id_generator = None

    def run(self):
        """Run this thread."""
        self.logger.debug(self._display_name + " is started")

        while not self.wait(1):
            self.monitor()

        self.logger.debug(self._display_name + " is stopped")

    def monitor(self) -> None:
        """Ensure processes are still alive.

        Iterate through all runners, restarting any processes that have stopped.

        Note:
            This must be done inside of the PluginManager class because of the
            process.poll() check. That can only be done from within this class.
        """
        for the_runner in self._runners:
            if self.stopped():
                break

            if the_runner.process and the_runner.process.poll() is not None:
                if the_runner.restart:
                    self.logger.warning(f"Runner {the_runner} stopped, restarting")
                    self._restart(the_runner)
                elif not the_runner.stopped and not the_runner.dead:
                    self.logger.warning(f"Runner {the_runner} is dead, not restarting")
                    the_runner.dead = True

    def plugin_path(self):
        return self._plugin_path

    def paths(self) -> List[str]:
        """Get all current runner paths."""
        return list({the_runner.process_cwd for the_runner in self._runners})

    def get_runner(self, runner_id: Optional[str] = None) -> Optional[Runner]:
        """Get a representation of a runner.

        Args:
            runner_id: The Runner ID to lookup, optional.

        Returns:
            The Runner associated with the provided ID or ``None`` if no argument was
            passed.
        """
        process_runner = (
            self._from_runner_id(runner_id) if runner_id is not None else None
        )

        if process_runner is not None:
            return process_runner.state()

        return None

    def get_runners(self) -> List[Runner]:
        """Get a representation of current runners."""
        return [the_runner.state() for the_runner in self._runners]

    def has_instance_id(self, instance_id: str) -> bool:
        """Determine if a given instance ID has an associated runner."""
        return self._from_instance_id(instance_id=instance_id) is not None

    def handle_initialize(self, event: Event) -> None:
        """Called whenever an INSTANCE_INITIALIZED occurs

        This associates the event instance with a specific runner.
        """
        runner_id = event.payload.metadata.get("runner_id")

        if runner_id is not None:
            instance = event.payload

            self.logger.debug(
                f"Associating runner ID ({runner_id}) with instance ID ({instance.id})"
            )

            the_runner = self._from_runner_id(runner_id)
            the_runner.associate(instance=instance)
            the_runner.restart = True

    def handle_stopped(self, event: Event) -> None:
        """Called whenever an INSTANCE_STOPPED occurs.

        If the event instance is associated with any runner that this PluginManager
        knows about then that runner will be marked as stopped and no longer monitored.
        """
        the_runner = self._from_instance_id(event.payload.id)

        if the_runner is not None:
            the_runner.stopped = True
            the_runner.restart = False
            the_runner.dead = False

    def restart(
        self, runner_id: Optional[str] = None, instance_id: Optional[str] = None
    ) -> Optional[Runner]:
        """Restart the runner for a particular Runner ID or Instance ID.

        Args:
            runner_id: An ID string associated with a Runner object, optional
            instance_id: An ID string associated with an Instance object, optional

        Returns:
            The Runner associated with the provided ID or ``None`` if neither argument
            is provided.
        """
        the_runner = None

        if runner_id is not None:
            the_runner = self._from_runner_id(runner_id)
        elif instance_id is not None:
            the_runner = self._from_instance_id(instance_id)

        return self._restart(the_runner).state() if the_runner is not None else None

    def update(
        self,
        runner_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        restart: Optional[bool] = None,
        stopped: Optional[bool] = None,
    ) -> Optional[Runner]:
        """Update a runner's state."""
        the_runner = None

        if runner_id is not None:
            the_runner = self._from_runner_id(runner_id)
        elif instance_id is not None:
            the_runner = self._from_instance_id(instance_id)

        if the_runner is None:
            return None

        if stopped is not None:
            the_runner.stopped = stopped
        if restart is not None:
            the_runner.restart = restart

        return the_runner.state()

    def stop_one(
        self,
        runner_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        send_sigterm: bool = True,
        remove: bool = False,  # noqa
    ) -> Runner:
        """Stop the runner for a given Runner ID or Instance ID.

        The PluginManager has no ability to places messages on the message queue, so
        it's possible that a stop message will already have been sent to the plugin
        that's being asked to stop. If that's NOT the case then send_sigterm should be
        set to True to attempt to stop the runner gracefully.

        This will wait for the runner to stop for plugin.local.timeout.shutdown seconds.
        If the runner is not stopped after that time its process will be killed with
        SIGKILL.

        Args:
            runner_id: The runner ID to stop, optional.
            instance_id: The instance ID to stop, optional.
            send_sigterm: If true, send SIGTERM before waiting. Defaults to ``True``.
            remove: Flag controlling if the runner should be removed from runner list.
                Defaults to ``False``.

        Returns:
            The stopped runner.
        """
        the_runner = None

        if runner_id is not None:
            the_runner = self._from_runner_id(runner_id)
        elif instance_id is not None:
            the_runner = self._from_instance_id(instance_id)

        if the_runner is None:
            raise Exception(
                f"Could not determine runner using runner ID ({runner_id}) and "
                f"instance ID ({instance_id})"
            )

        if send_sigterm:
            the_runner.term()

        the_runner.join(config.get("plugin.local.timeout.shutdown"))

        if the_runner.is_alive():
            the_runner.dead = True
            the_runner.kill()

        the_runner.stopped = True
        the_runner.restart = False

        if remove:
            self._runners.remove(the_runner)

        return the_runner.state()

    def stop_all(self) -> None:
        """Stop all known runners."""
        return self._stop_multiple(self._runners)

    def scan_path(self, paths: Optional[Iterable[Path]] = None) -> List[Runner]:
        """Scan a directory for valid plugins.

        Note:
            This scan does not walk the directory tree--all plugins must be in the
            top-level of the given path.

        Args:
            paths: The paths to scan, Optional. If ``None``, will be all subdirectories
                of the plugin path specified at initialization

        Returns:
            List of Runners to run the plugins.
        """
        if paths is None and self._plugin_path is None:
            self.logger.error("PluginManager.scan_path has no path to scan")
            return []

        plugin_paths = paths or self._plugin_path.iterdir()
        new_runners = []

        try:
            for path in plugin_paths:
                try:
                    if self._is_valid_plugin_path(path, self.paths(), self.logger):
                        new_runners += self._create_runners(path)
                except Exception as ex:
                    self.logger.exception(f"Error loading plugin at {path}: {ex}")

        except Exception as ex:
            self.logger.exception(f"Error scanning plugin path: {ex}")

        return [the_runner.state() for the_runner in new_runners]

    @staticmethod
    def _is_valid_plugin_path(
        path: Optional[Path], known_paths: List[str], the_logger: logging.Logger
    ) -> bool:
        try:
            if path is None:
                raise PluginValidationError("malformed plugin path, NoneType")

            path_parts = path.parts

            if len(path_parts) == 0:
                raise PluginValidationError("empty path")
            if path_parts[-1].startswith("."):
                raise PluginValidationError("hidden file")

            if not path.exists():
                raise PluginValidationError("does not exist")
            if not path.is_dir():
                raise PluginValidationError("not a directory")

            config_file = path / CONFIG_NAME

            if not config_file.exists():
                raise PluginValidationError(f"config file {config_file} does not exist")
            if not config_file.is_file():
                raise PluginValidationError(f"config file {config_file} is not a file")

            return path not in known_paths
        except PluginValidationError as plugin_error:
            the_logger.warning(
                "Not loading plugin at %s: %s" % (str(path), str(plugin_error))
            )
            return False

    def _from_instance_id(self, instance_id: str) -> Optional[ProcessRunner]:
        for the_runner in self._runners:
            if the_runner.instance_id == instance_id:
                return the_runner

        return None

    def _from_runner_id(self, runner_id: str) -> Optional[ProcessRunner]:
        for the_runner in self._runners:
            if the_runner.runner_id == runner_id:
                return the_runner

        return None

    def _restart(self, the_runner: ProcessRunner) -> ProcessRunner:
        new_runner = ProcessRunner(
            runner_id=the_runner.runner_id,
            process_args=the_runner.process_args,
            process_cwd=the_runner.process_cwd,
            process_env=the_runner.process_env,
            capture_streams=the_runner.capture_streams,
        )

        self._runners.remove(the_runner)
        self._runners.append(new_runner)

        new_runner.start()

        return new_runner

    def _stop_multiple(
        self, the_runners: Optional[Iterable[ProcessRunner]] = None
    ) -> None:
        # If not specified, default to all runners
        if the_runners is None:
            the_runners = self._runners

        # If empty, we're done
        if len(the_runners) == 0:
            return

        shutdown_pool = ThreadPoolExecutor(len(the_runners))
        stop_futures: List[Future] = []

        for the_runner in the_runners:
            stop_futures.append(
                shutdown_pool.submit(
                    self.stop_one, runner_id=the_runner.runner_id, send_sigterm=True
                )
            )

        wait(stop_futures)

        for the_runner in the_runners:
            self._runners.remove(the_runner)

    def _get_runner_id(self) -> str:
        """Get a 10-letter string to serve as a runner ID."""
        if self._runner_id_generator is None:
            self._runner_id_generator = self._runner_id_generator_factory()
        return next(self._runner_id_generator)

    @staticmethod
    def _runner_id_generator_factory() -> str:
        """Will not yield the same result twice, but is theoretically less than
        ideal because of a potentially long-running loop. In any case, a solution
        that removes this defect is heavy-weight (absent *numpy*) and is judged to not
        be worth the initial effort nor the maintenance for this application.
        """

        def _runner_id():
            return "".join([choice(string.ascii_letters) for _ in range(10)])

        seen = set()

        while True:
            runner_id = _runner_id()

            while runner_id in seen:
                runner_id = _runner_id()

            seen.add(runner_id)

            yield runner_id

    def _create_runners(self, plugin_path: Path) -> List[ProcessRunner]:
        """Create and start ProcessRunners for a particular directory.

        Uses the validator to validate the config.

        Args:
            plugin_path: The path of the plugin.

        Returns:
            List of newly created runners.

        """
        new_runners = []

        try:
            plugin_config = ConfigLoader.load(plugin_path / CONFIG_NAME)
        except PluginValidationError as ex:
            self.logger.error(f"Error loading config for plugin at {plugin_path}: {ex}")
            return new_runners

        for instance_name in plugin_config["INSTANCES"]:
            runner_id = self._get_runner_id()
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

        for the_runner in new_runners:
            self.logger.debug(f"Starting runner {the_runner}")
            the_runner.start()

        # as obnoxious as it is to have a sleep here, we have to wait for the
        # threads to complete their run() methods before we know whether they're dead
        # or not; smaller values were tried but were not reliable
        time.sleep(1)

        return new_runners

    @staticmethod
    def _process_args(plugin_config: Dict[str, Any], instance_name: str):
        interp_path = plugin_config.get("INTERPRETER_PATH")
        process_args = [interp_path] if interp_path is not None else [sys.executable]

        plugin_entry = plugin_config.get("PLUGIN_ENTRY")

        if plugin_entry is not None:
            process_args += plugin_entry.split(" ")
        else:
            plugin_name = plugin_config.get("NAME")

            if plugin_name is not None:
                process_args += ["-m", plugin_name]
            else:
                raise PluginValidationError("Can't generate process args")

        plugin_args = plugin_config["PLUGIN_ARGS"].get(instance_name)

        if plugin_args is not None:
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

        # Warn if the normalized beer.conf will result in 0 instances
        if not len(config_dict["INSTANCES"]):
            logger.warning(
                f"Config file {config_file} resulted in an empty instance list, which "
                "means no plugins will be started. This is normally caused by "
                "INSTANCES=[] or PLUGIN_ARGS={} lines in beer.conf. If this is not "
                "what you want please remove those lines."
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
            f"{ConfigKeys.PLUGIN_ENTRY.name} '{entry_point}' must be a Python file or a"
            " runnable package"
        )

    @staticmethod
    def _instances(config_module) -> None:
        instances = getattr(config_module, ConfigKeys.INSTANCES.name, None)

        if instances is not None and not isinstance(instances, list):
            raise PluginValidationError(
                f"Invalid {ConfigKeys.INSTANCES.name} entry '{instances}': if present"
                " it must be a list"
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
                f"Invalid {ConfigKeys.PLUGIN_ARGS.name} '{args}': must be a list or"
                " dict"
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
                f"Invalid {ConfigKeys.ENVIRONMENT.name} entry '{env}': if present it"
                " must be a dict"
            )

        for key, value in env.items():
            if not isinstance(key, str):
                raise PluginValidationError(
                    f"Invalid {ConfigKeys.ENVIRONMENT.name} key '{key}': must be a"
                    " string"
                )

            if not isinstance(value, str):
                raise PluginValidationError(
                    f"Invalid {ConfigKeys.ENVIRONMENT.name} value '{value}': must be a"
                    " string"
                )

            if key.startswith("BG_"):
                raise PluginValidationError(
                    f"Invalid {ConfigKeys.ENVIRONMENT.name} key '{key}': Can't specify"
                    " an environment variable with a 'BG_' prefix as it can mess with"
                    " internal Beer-garden machinery. Sorry about that :/"
                )
