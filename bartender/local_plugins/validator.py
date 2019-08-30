import logging
import sys
from imp import load_source
from os.path import isdir, isfile, join

from bartender.errors import PluginValidationError


class LocalPluginValidator(object):
    """Class Used for Validating Local Plugins"""

    CONFIG_NAME = "beer.conf"
    NAME_KEY = "NAME"
    VERSION_KEY = "VERSION"
    ENTRY_POINT_KEY = "PLUGIN_ENTRY"
    INSTANCES_KEY = "INSTANCES"
    ARGS_KEY = "PLUGIN_ARGS"
    REQUIRED_KEYS = [NAME_KEY, VERSION_KEY, ENTRY_POINT_KEY]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_plugin(self, path_to_plugin):
        """Validates a Plugin and its arguments

        :param path_to_plugin:
        :return:
        """
        try:
            self.logger.debug("Validating Plugin at %s ", path_to_plugin)

            self.validate_plugin_path(path_to_plugin)
            self.logger.debug("Validated Plugin Path successfully.")
            self.validate_plugin_config(path_to_plugin)
            self.logger.debug("Validated Plugin Config successfully.")

            self.logger.debug("Successfully validated Plugin at %s", path_to_plugin)
            return True

        except PluginValidationError as pve:
            self.logger.error(
                "Validation error occurred on plugin located at : %s", path_to_plugin
            )
            self.logger.error(str(pve))
            return False
        finally:
            if "BGPLUGINCONFIG" in sys.modules:
                del sys.modules["BGPLUGINCONFIG"]

    def validate_plugin_path(self, path_to_plugin):
        """Validates that a plugin path is actually a path and not a single file."""
        if path_to_plugin is None or not isdir(path_to_plugin):
            raise PluginValidationError(
                'Plugin path "%s" is not a directory' % path_to_plugin
            )

        return True

    def validate_plugin_config(self, path_to_plugin):
        """Validates that there is a beer.conf file in the path_to_plugin

        :param path_to_plugin: Path to the plugin
        :return: True if beer.conf exists
        :raises: PluginValidationError if beer.conf is not found
        """
        if path_to_plugin is None:
            raise PluginValidationError(
                "Attempted to validate plugin config, " "but the plugin_path is None."
            )

        path_to_config = join(path_to_plugin, self.CONFIG_NAME)

        if not isfile(path_to_config):
            raise PluginValidationError(
                "Could not validate config file. It does not exist."
            )

        config_module = self._load_plugin_config(path_to_plugin)
        self.validate_required_config_keys(config_module)
        self.logger.debug("Required keys are present.")
        self.validate_entry_point(config_module, path_to_plugin)
        self.logger.debug("Validated Plugin Entry Point successfully.")
        self.validate_instances_and_args(config_module)
        self.logger.debug("Validated plugin instances & arguments successfully.")
        self.validate_plugin_environment(config_module)
        self.logger.debug("Validated Plugin Environment successfully.")
        return True

    def validate_required_config_keys(self, config_module):
        if config_module is None:
            raise PluginValidationError("Configuration is None. This is not allowed.")

        for key in self.REQUIRED_KEYS:
            if not hasattr(config_module, key):
                raise PluginValidationError(
                    "Required key '%s' is not present. " "This is not allowed." % key
                )

    def _load_plugin_config(self, path_to_plugin):
        """Loads an already validated plugin Config.

        That is, it assumes path_to_config will exist and that it can load it succesfully"""
        path_to_config = join(path_to_plugin, self.CONFIG_NAME)

        return load_source("BGPLUGINCONFIG", path_to_config)

    def validate_entry_point(self, config_module, path_to_plugin):
        """Validates a plugin's entry point. Returns True or throws a PluginValidationError

        An entry point is considered valid if the config has an entry with key PLUGIN_ENTRY
        and the value is a path to either a file or the name of a runnable Python module.

        :param config_module: The previously loaded configuration for the plugin
        :param path_to_plugin: The path to the root of the plugin
        """
        if config_module is None:
            raise PluginValidationError("Configuration is None. This is not allowed.")

        if path_to_plugin is None:
            raise PluginValidationError("Path to Plugin is None. This is not allowed.")

        if not hasattr(config_module, self.ENTRY_POINT_KEY):
            raise PluginValidationError(
                "No %s defined in the plugin configuration." % self.ENTRY_POINT_KEY
            )

        entry_point = getattr(config_module, self.ENTRY_POINT_KEY)

        if isfile(join(path_to_plugin, entry_point)):
            return
        elif entry_point.startswith("-m "):
            pkg_path = join(path_to_plugin, entry_point[3:])
            if (
                isdir(pkg_path)
                and isfile(join(pkg_path, "__init__.py"))
                and isfile(join(pkg_path, "__main__.py"))
            ):
                return
        else:
            raise PluginValidationError(
                "The %s must be a Python script or a runnable Python package: %s"
                % (self.ENTRY_POINT_KEY, entry_point)
            )

    def validate_instances_and_args(self, config_module):
        if config_module is None:
            raise PluginValidationError("Configuration is None. This is not allowed.")

        plugin_args = getattr(config_module, self.ARGS_KEY, None)
        instances = getattr(config_module, self.INSTANCES_KEY, None)

        if instances is not None and not isinstance(instances, list):
            raise PluginValidationError(
                "'%s' entry was not None or a list. This is invalid. "
                "Got: %s" % (self.INSTANCES_KEY, instances)
            )

        if plugin_args is None:
            return True
        elif isinstance(plugin_args, list):
            return self.validate_individual_plugin_arguments(plugin_args)
        elif isinstance(plugin_args, dict):
            for instance_name, instance_args in plugin_args.items():
                if instances is not None and instance_name not in instances:
                    raise PluginValidationError(
                        "'%s' contains key '%s' but that instance is not specified in the '%s'"
                        "entry." % (self.ARGS_KEY, instance_name, self.INSTANCES_KEY)
                    )
                self.validate_individual_plugin_arguments(instance_args)

            if instances:
                for instance_name in instances:
                    if instance_name not in plugin_args.keys():
                        raise PluginValidationError(
                            "'%s' contains key '%s' but that instance is not specified in the "
                            "'%s' entry."
                            % (self.INSTANCES_KEY, instance_name, self.ARGS_KEY)
                        )

            return True
        else:
            raise PluginValidationError(
                "'%s' entry was not a list or dictionary. This is invalid. "
                "Got: %s" % (self.ARGS_KEY, plugin_args)
            )

    def validate_individual_plugin_arguments(self, plugin_args):
        """Validates an individual PLUGIN_ARGS entry"""

        if plugin_args is not None and not isinstance(plugin_args, list):
            self.logger.error(
                "Invalid Plugin Argument Specified. It was not a list or None. "
                "This is not allowed"
            )
            raise PluginValidationError(
                "Invalid Plugin Argument Specified: %s. It was not a "
                "list or None. This is not allowed." % plugin_args
            )

        if isinstance(plugin_args, list):
            for plugin_arg in plugin_args:
                if not isinstance(plugin_arg, str):
                    self.logger.error(
                        "Invalid plugin argument: %s - this argument must be a string",
                        plugin_arg,
                    )
                    raise PluginValidationError(
                        "Invalid plugin argument: %s - this argument must be a string."
                        % plugin_arg
                    )

        return True

    def validate_plugin_environment(self, config_module):
        """Validates ENVIRONMENT if specified.

        ENVIRONMENT must be a dictionary of Strings to Strings. Otherwise it is invalid.

        :param config_module:
        :return: True if valid
        :raises: PluginValidationError if something goes wrong while validating
        """
        if config_module is None:
            self.logger.error("Configuration is None. This is not allowed.")
            raise PluginValidationError("Configuration is None. This is not allowed.")

        if hasattr(config_module, "ENVIRONMENT"):
            env = config_module.ENVIRONMENT
            if not isinstance(env, dict):
                self.logger.error(
                    "Invalid ENVIRONMENT specified: %s. This argument must "
                    "be a dictionary.",
                    env,
                )
                raise PluginValidationError(
                    "Invalid ENVIRONMENT specified: %s. This argument "
                    "must be a dictionary." % env
                )

            for key, value in env.items():
                if not isinstance(key, str):
                    self.logger.error(
                        "Invalid Key: %s specified for plugin environment. "
                        "This must be a String.",
                        key,
                    )
                    raise PluginValidationError(
                        "Invalid Key: %s specified for plugin "
                        "environment. This must be a String." % key
                    )

                if key.startswith("BG_"):
                    self.logger.error(
                        "Invalid key: %s specified for plugin environment. The 'BG_' prefix is a "
                        "special case for beer-garden only environment variables. You will have to "
                        "pick another name. Sorry for the inconvenience." % key
                    )
                    raise PluginValidationError(
                        "Invalid key: %s specified for plugin environment. The 'BG_' prefix "
                        "is a special case for beer-garden only environment variables. You will "
                        "have to pick another name. Sorry for the inconvenience." % key
                    )

                if not isinstance(value, str):
                    self.logger.error(
                        "Invalid Key: %s specified for plugin environment. This must be a String.",
                        value,
                    )
                    raise PluginValidationError(
                        "Invalid Value: %s specified for plugin environment. This must be a "
                        "String." % value
                    )

        return True
