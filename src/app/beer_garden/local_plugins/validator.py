# -*- coding: utf-8 -*-

import logging
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from beer_garden.errors import PluginValidationError

logger = logging.getLogger(__name__)

CONFIG_NAME = "beer.conf"
NAME_KEY = "NAME"
VERSION_KEY = "VERSION"
ENTRY_POINT_KEY = "PLUGIN_ENTRY"
INSTANCES_KEY = "INSTANCES"
ARGS_KEY = "PLUGIN_ARGS"
ENVIRONMENT_KEY = "ENVIRONMENT"
REQUIRED_KEYS = [NAME_KEY, VERSION_KEY, ENTRY_POINT_KEY]


def validate_plugin(path: Path) -> bool:
    """Validate a plugin directory is valid

    Args:
        path: The path where the plugin lives

    Returns:
        True: Validation was successful
        False: Validation was not successful

    """
    try:
        if not path or not path.is_dir():
            raise PluginValidationError(f"Plugin path {path} is not a directory")

        config_file = path / CONFIG_NAME

        if not config_file.exists():
            raise PluginValidationError("Config file does not exist")

        if not config_file.is_file():
            raise PluginValidationError("Config file is not actually a file")

        # Need to construct our own Loader here, the default doesn't work with .conf
        loader = SourceFileLoader("bg_plugin_config", str(config_file))
        spec = spec_from_file_location("bg_plugin_config", config_file, loader=loader)
        config_module = module_from_spec(spec)
        spec.loader.exec_module(config_module)

        if config_module is None:
            raise PluginValidationError(f"Error loading config module {CONFIG_NAME}")

        _required_keys(config_module)
        _entry_point(config_module, path)
        _instances(config_module)
        _args(config_module)
        _environment(config_module)
    except PluginValidationError as ex:
        logger.exception(f"Error while validating plugin at {path}: {ex}")
        return False
    finally:
        if "BGPLUGINCONFIG" in sys.modules:
            del sys.modules["BGPLUGINCONFIG"]

    return True


def _required_keys(config_module) -> None:
    for key in REQUIRED_KEYS:
        if not hasattr(config_module, key):
            raise PluginValidationError(f"Required key '{key}' is not present")


def _entry_point(config_module, path: Path) -> None:
    """Validates a plugin's entry point.

    An entry point is considered valid if the config has an entry with key
    PLUGIN_ENTRY and the value is a path to either a file or the name of a runnable
    Python module.
    """
    entry_point = getattr(config_module, ENTRY_POINT_KEY)

    if (path / entry_point).exists():
        return

    if entry_point.startswith("-m "):
        pkg_path = path / entry_point[3:]

        if (
            pkg_path.is_dir()
            and (pkg_path / "__init__.py").is_file()
            and (pkg_path / "__main__.py").is_file()
        ):
            return

    raise PluginValidationError(
        f"{ENTRY_POINT_KEY} '{entry_point}' must be a Python file or a runnable package"
    )


def _instances(config_module) -> None:
    instances = getattr(config_module, INSTANCES_KEY, None)

    if instances is not None and not isinstance(instances, list):
        raise PluginValidationError(
            f"Invalid {INSTANCES_KEY} entry '{instances}': if present it must be a list"
        )


def _args(config_module) -> None:
    args = getattr(config_module, ARGS_KEY, None)

    if args is None:
        return

    if isinstance(args, list):
        _individual_args(args)

    elif isinstance(args, dict):
        instances = getattr(config_module, INSTANCES_KEY)

        for instance_name, instance_args in args.items():
            if instances is not None and instance_name not in instances:
                raise PluginValidationError(
                    f"{ARGS_KEY} contains key '{instance_name}' but that instance is "
                    f"not specified in the {INSTANCES_KEY} entry"
                )

            _individual_args(instance_args)

        if instances:
            for instance_name in instances:
                if instance_name not in args.keys():
                    raise PluginValidationError(
                        f"{INSTANCES_KEY} contains '{instance_name}' but that instance "
                        f"is not specified in the {ARGS_KEY} entry."
                    )

    else:
        raise PluginValidationError(
            f"Invalid {ARGS_KEY} entry '{args}': valid types are list, dict"
        )


def _individual_args(args) -> None:
    """Validates an individual PLUGIN_ARGS entry"""
    if args is None:
        return

    if not isinstance(args, list):
        raise PluginValidationError(
            f"Invalid {ARGS_KEY} entry '{args}': must be a list"
        )

    for arg in args:
        if not isinstance(arg, str):
            raise PluginValidationError(
                f"Invalid plugin argument '{arg}': must be a string"
            )


def _environment(config_module) -> None:
    """Validates ENVIRONMENT if specified.

    ENVIRONMENT must be a dictionary of Strings to Strings. Otherwise it is invalid.
    """
    env = getattr(config_module, ENVIRONMENT_KEY, None)

    if env is None:
        return

    if not isinstance(env, dict):
        raise PluginValidationError(
            f"Invalid {ENVIRONMENT_KEY} entry '{env}': if present it must be a dict"
        )

    for key, value in env.items():
        if not isinstance(key, str):
            raise PluginValidationError(
                f"Invalid {ENVIRONMENT_KEY} key '{key}': must be a string"
            )

        if not isinstance(value, str):
            raise PluginValidationError(
                f"Invalid {ENVIRONMENT_KEY} value '{value}': must be a string"
            )

        if key.startswith("BG_"):
            raise PluginValidationError(
                f"Invalid {ENVIRONMENT_KEY} key '{key}': Can't specify an environment "
                f"variable with a 'BG_' prefix as it can mess with internal "
                f"Beer-garden machinery. Sorry about that :/"
            )
