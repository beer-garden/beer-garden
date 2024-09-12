# -*- coding: utf-8 -*-
"""Log Service

The log service is responsible for:

* Loading custom logger files
* Generating default logging configurations
* Manages logging configurations for Plugins and Beer Garden application
"""

import copy
import logging
import logging.config
import logging.handlers
from typing import Any, Dict

import brewtils.log
from brewtils.models import Events
from ruamel import yaml
from ruamel.yaml import YAML

import beer_garden.config as config

logger = logging.getLogger(__name__)

# Overall application logging configuration
_APP_LOGGING = None

_default_formatter = {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}

_stdout_handler = {
    "class": "logging.StreamHandler",
    "formatter": "default",
    "stream": "ext://sys.stdout",
}

_file_handler = {
    "class": "logging.handlers.RotatingFileHandler",
    "backupCount": 5,
    "encoding": "utf8",
    "formatter": "default",
    "maxBytes": 10485760,
}

_config_base: Dict[Any, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": _default_formatter},
    "handlers": {},
    "root": {"level": "INFO", "formatter": "default", "handlers": []},
}


def load(config: dict, force=False) -> None:
    """Load the application logging configuration.

    Will attempt to use a file specified by the log_config_file config item. If that
    item resolves to None then will use the "default" logging configuration with the
    values from the log_level and log_file configuration items.

    Args:
        config: Subsection "log" of the loaded configuration
        force: Force a reload.
    """
    global _APP_LOGGING
    if _APP_LOGGING is not None and not force:
        return

    logging_filename = config.get("config_file")

    if logging_filename:
        with open(logging_filename, "rt") as log_file:
            logging_config = YAML().load(log_file)
    else:
        logging_config = default_app_config(
            config.get("fallback_level"), config.get("fallback_file")
        )

    logging.config.dictConfig(logging_config)

    _APP_LOGGING = logging_config


def default_app_config(level=None, filename=None):
    app_config = copy.deepcopy(_config_base)

    if filename:
        app_config["handlers"]["file"] = copy.deepcopy(_file_handler)
        app_config["handlers"]["file"]["filename"] = filename
        app_config["handlers"]["file"]["backupCount"] = 20

        app_config["root"]["handlers"].append("file")
    else:
        app_config["handlers"]["stdout"] = copy.deepcopy(_stdout_handler)
        app_config["root"]["handlers"].append("stdout")

    app_config["loggers"] = {
        "pika": {"level": "ERROR"},
        "requests.packages.urllib3.connectionpool": {"level": "WARN"},
        "tornado.access": {"level": "WARN"},
        "tornado.application": {"level": "WARN"},
        "tornado.general": {"level": "WARN"},
    }

    if level:
        app_config["root"]["level"] = level

    return app_config


def default_plugin_config(level=None, stdout=True, file=True, filename=None):
    plugin_config = copy.deepcopy(_config_base)

    if stdout:
        plugin_config["handlers"]["stdout"] = copy.deepcopy(_stdout_handler)
        plugin_config["root"]["handlers"].append("stdout")

    if file:
        plugin_config["handlers"]["file"] = copy.deepcopy(_file_handler)
        plugin_config["handlers"]["file"]["filename"] = (
            filename or "log/%(instance_name)s.log"
        )
        plugin_config["root"]["handlers"].append("file")

    if level:
        plugin_config["root"]["level"] = level

    return plugin_config


def process_record(record):
    """Handle a log record.

    Intended to be used as the ``action`` kwarg of a QueueListener.
    """
    logger = logging.getLogger(record.name)

    if logger.isEnabledFor(record.levelno):
        logger.handle(record)


def setup_entry_point_logging(queue):
    """Set up logging for an entry point process"""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "entry_point": {
                    "class": "logging.handlers.QueueHandler",
                    "level": "DEBUG",
                    "queue": queue,
                }
            },
            "root": {"level": "DEBUG", "handlers": ["entry_point"]},
        }
    )


def get_plugin_log_config(**kwargs) -> dict:
    """Get the plugin logging configuration

    Args:
        **_: Eventually you will be able to select a plugin logging config based on
            selectors (system name, etc.)

    Returns:
        The plugin logging configuration
    """
    return PluginLoggingManager.get(**kwargs)


def get_plugin_log_config_legacy() -> dict:
    """Get the old-style plugin logging configuration

    Returns:
        The plugin logging configuration
    """
    return PluginLoggingManager.get_legacy()


def load_plugin_log_config():
    local_default = brewtils.log.default_config(
        level=config.get("plugin.local.logging.fallback_level")
    )
    remote_default = brewtils.log.default_config(
        level=config.get("plugin.remote.logging.fallback_level")
    )

    PluginLoggingManager.load(
        local_default=local_default,
        remote_default=remote_default,
        local_file=config.get("plugin.local.logging.config_file"),
        remote_file=config.get("plugin.remote.logging.config_file"),
    )


class PluginLoggingManager(object):
    """A class for loading plugin logging configuration from files.

    Usually used by simply calling `load`. If given a config_file, it will attempt to
    create a valid logging configuration object from the file given. If no file is
    given it will fallback to default_config. This is assumed to be a valid python
    logging configuration dict (i.e. something you would pass to `logging.dictConfig`).

    If local_file is given then a separate configuration will be loaded that will be
    used for local plugins. Otherwise the same configuration will be used for both local
    and remote plugins.
    """

    # Actual logging configuration
    _REMOTE_CONFIG: dict = None
    _LOCAL_CONFIG: dict = None

    @classmethod
    def get(cls, **kwargs) -> dict:
        """Get the logging config"""
        return cls._LOCAL_CONFIG if kwargs.get("local") else cls._REMOTE_CONFIG

    @classmethod
    def load(
        cls,
        local_default: dict,
        remote_default: dict,
        local_file: str,
        remote_file: str,
    ) -> None:
        """Load the logging configuration

        If no config_file is given, will fallback to the default config passed in.

        Args:
            local_default: Fallback local configuration
            remote_default: Fallback remote configuration
            local_file: Logging configuration file to load for local plugins
            remote_file: Logging configuration file to load for remote plugins

        Returns:
            None
        """
        if remote_file:
            with open(remote_file) as log_config_file:
                cls._REMOTE_CONFIG = yaml.safe_load(log_config_file)
        else:
            cls._REMOTE_CONFIG = remote_default

        if local_file:
            with open(local_file) as log_config_file:
                cls._LOCAL_CONFIG = yaml.safe_load(log_config_file)
        else:
            cls._LOCAL_CONFIG = local_default

    @classmethod
    def get_legacy(cls):
        """Get configuration in the old LoggingConfig format"""
        log_config = copy.deepcopy(cls._REMOTE_CONFIG)

        if "version" in log_config:
            del log_config["version"]
        if "disable_existing_loggers" in log_config:
            del log_config["disable_existing_loggers"]

        level = config.get("plugin.logging.fallback_level")
        if "root" in log_config:
            if "level" in log_config["root"]:
                level = log_config["root"]["level"]

            del log_config["root"]

        log_config["level"] = level

        return log_config


def handle_event(event):
    """Only care about local garden"""
    if event.garden == config.get("garden.name"):
        if event.name == Events.PLUGIN_LOGGER_FILE_CHANGE.name:
            logger.info("Detected change to plugin logging config file, reloading")
            load_plugin_log_config()
