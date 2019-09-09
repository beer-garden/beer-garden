import logging.config

from box import Box
from ruamel.yaml import YAML

import beer_garden
from beer_garden.bg_utils.plugin_logging_loader import PluginLoggingLoader

plugin_logging_config = None
_LOGGING_CONFIG = None


def load(config: Box, force=False) -> dict:
    """Load the application logging configuration.

    Will attempt to use a file specified by the log_config_file config item. If that
    item resolves to None then will use the "default" logging configuration with the
    values from the log_level and log_file configuration items.

    Args:
        config: Subsection "log" of the loaded configuration
        force: Force a reload.

    Returns:
        The loaded logging configuration

    """
    global _LOGGING_CONFIG
    if _LOGGING_CONFIG is not None and not force:
        return _LOGGING_CONFIG

    logging_filename = config.get("config_file")

    if logging_filename:
        with open(logging_filename, "rt") as log_file:
            logging_config = YAML().load(log_file)
    else:
        logging_config = default_app_config(config.get("level"), config.get("file"))

    logging.config.dictConfig(logging_config)

    _LOGGING_CONFIG = logging_config

    return _LOGGING_CONFIG


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


def get_plugin_log_config(system_name=None):
    return plugin_logging_config.get_plugin_log_config(system_name=system_name)


def load_plugin_log_config():
    global plugin_logging_config

    plugin_config = beer_garden.config.get("plugin")
    plugin_logging_config = PluginLoggingLoader().load(
        filename=plugin_config.logging.config_file,
        level=plugin_config.logging.level,
        default_config=_LOGGING_CONFIG,
    )
