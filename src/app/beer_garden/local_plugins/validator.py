# -*- coding: utf-8 -*-

from pathlib import Path
from types import ModuleType

from beer_garden.errors import PluginValidationError
from beer_garden.local_plugins import ConfigKeys


def validate_config(config_module: ModuleType, path: Path) -> None:
    """Validate a plugin directory is valid

    Args:
        config_module: Configuration module to validate
        path: Path to directory containing plugin

    Returns:
        None

    Raises:
        PluginValidationError: Validation was not successful

    """
    _entry_point(config_module, path)
    _instances(config_module)
    _args(config_module)
    _environment(config_module)


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


def _instances(config_module) -> None:
    instances = getattr(config_module, ConfigKeys.INSTANCES.name, None)

    if instances is not None and not isinstance(instances, list):
        raise PluginValidationError(
            f"Invalid {ConfigKeys.INSTANCES.name} entry '{instances}': if present it "
            f"must be a list"
        )


def _args(config_module) -> None:
    args = getattr(config_module, ConfigKeys.PLUGIN_ARGS.name, None)

    if args is None:
        return

    if isinstance(args, list):
        _individual_args(args)

    elif isinstance(args, dict):
        instances = getattr(config_module, ConfigKeys.INSTANCES.name)

        for instance_name, instance_args in args.items():
            if instances is not None and instance_name not in instances:
                raise PluginValidationError(
                    f"{ConfigKeys.PLUGIN_ARGS.name} contains key '{instance_name}' but "
                    f"that instance is not in {ConfigKeys.INSTANCES.name}"
                )

            _individual_args(instance_args)

        if instances:
            for instance_name in instances:
                if instance_name not in args.keys():
                    raise PluginValidationError(
                        f"{ConfigKeys.INSTANCES.name} contains '{instance_name}' but "
                        f"that instance is not in {ConfigKeys.PLUGIN_ARGS.name}"
                    )

    else:
        raise PluginValidationError(
            f"Invalid {ConfigKeys.PLUGIN_ARGS.name} '{args}': must be a list or dict"
        )


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
