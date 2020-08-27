# -*- coding: utf-8 -*-
import copy

import brewtils.log
import logging
import logging.config
import logging.handlers
from ruamel import yaml
from ruamel.yaml import YAML

import beer_garden.config as config

_APP_LOGGING = None


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
        logging_config = default_app_config(config.get("level"), config.get("file"))

    logging.config.dictConfig(logging_config)

    _APP_LOGGING = logging_config


def default_app_config(level, filename=None):
    if filename:
        handler = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "simple",
            "filename": filename,
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8",
        }
    else:
        handler = {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": level,
            "stream": "ext://sys.stdout",
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        "handlers": {"beer_garden": handler},
        "loggers": {
            "pika": {"level": "ERROR"},
            "requests.packages.urllib3.connectionpool": {"level": "WARN"},
            "tornado.access": {"level": "WARN"},
            "tornado.application": {"level": "WARN"},
            "tornado.general": {"level": "WARN"},
        },
        "root": {"level": level, "handlers": ["beer_garden"]},
    }


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


def get_plugin_log_config(**_) -> dict:
    """Get the plugin logging configuration

    Args:
        **_: Eventually you will be able to select a plugin logging config based on
            selectors (system name, etc.)

    Returns:
        The plugin logging configuration
    """
    return PluginLoggingManager.get()


def get_plugin_log_config_legacy() -> dict:
    """Get the old-style plugin logging configuration

    Returns:
        The plugin logging configuration
    """
    return PluginLoggingManager.get_legacy()


def load_plugin_log_config():
    PluginLoggingManager.load(
        filename=config.get("plugin.logging.config_file"),
        default_config=brewtils.log.default_config(
            level=config.get("plugin.logging.fallback_level")
        ),
    )


class PluginLoggingManager(object):
    """A class for loading plugin logging configuration from files.

    Usually used by simply calling `load`. If given a filename, it will attempt to pull
    a valid logging configuration object from the file given. If no file was given, it
    will fall-back to the default configuration. This is assumed to be a valid python
    logging configuration dict (i.e. something you would pass to `logging.dictConfig`).

    """

    # Actual logging configuration
    _PLUGIN_LOGGING: dict = None

    @classmethod
    def get(cls) -> dict:
        """Get the logging config"""
        return cls._PLUGIN_LOGGING

    @classmethod
    def load(cls, filename: str, default_config) -> None:
        """Load the logging configuration

        If no filename is given, will fallback to the default config passed in.

        Args:
            filename: Filename of the plugin logging configuration to load
            default_config: Fallback configuration for if no filename is given

        Returns:
            None
        """
        if filename:
            with open(filename) as log_config_file:
                cls._PLUGIN_LOGGING = yaml.safe_load(log_config_file)
        else:
            cls._PLUGIN_LOGGING = default_config

    @classmethod
    def get_legacy(cls):
        """Get configuration in the old LoggingConfig format"""
        log_config = copy.deepcopy(cls._PLUGIN_LOGGING)

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
