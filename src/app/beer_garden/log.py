# -*- coding: utf-8 -*-
import copy
import logging
import logging.config
import logging.handlers
import string

import brewtils.log
import six
from brewtils.models import LoggingConfig
from ruamel import yaml
from ruamel.yaml import YAML

import beer_garden.config as config
from beer_garden.errors import LoggingLoadingError

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


def load_plugin_log_config():
    plugin_config = config.get("plugin")

    PluginLoggingManager.load(
        filename=plugin_config.logging.config_file,
        level=plugin_config.logging.level,
        default_config=brewtils.log.default_config(level="INFO"),
    )


def reload_plugin_log_config():
    load_plugin_log_config()

    return get_plugin_log_config()


class PluginLoggingManager(object):
    """A class for loading plugin logging configuration from files.

    Usually used by simply calling `load`. If given a filename, it will attempt to pull
    a valid logging configuration object from the file given. If no file was given, it
    will fall-back to the default configuration. This is assumed to be a valid python
    logging configuration dict (i.e. something you would pass to `logging.dictConfig`).

    """

    # Actual logging configuration
    _PLUGIN_LOGGING: dict = None

    STDOUT_HANDLERS = ["logging.StreamHandler"]
    LOGSTASH_HANDLERS = ["logstash_async.handler.AsynchronousLogstashHandler"]
    FILE_HANDLERS = [
        "logging.handlers.FileHandler",
        "logging.handlers.RotatingFileHandler",
        "logging.handlers.TimedRotatingFileHandler",
    ]
    KNOWN_HANDLERS = STDOUT_HANDLERS + LOGSTASH_HANDLERS + FILE_HANDLERS

    logger = logging.getLogger(__name__)

    @classmethod
    def get(cls) -> dict:
        """Get the logging config"""
        return cls._PLUGIN_LOGGING

    @classmethod
    def load(cls, filename: str, level: str, default_config) -> None:
        """Load the logging configuration

        If no filename is given, will fallback to the default config passed in.

        Args:
            filename: Filename of the plugin logging configuration to load
            level: A default level for the loggers
            default_config: Fallback configuration for if no filename is given

        Returns:
            None
        """
        raw_config = {}

        if filename:
            with open(filename) as log_config_file:
                raw_config = yaml.safe_load(log_config_file)

        # If no config could be found from a file use the default
        if not raw_config:
            raw_config = cls._parse_python_logging_config(default_config, level)

        cls.validate_config(raw_config, level)

        cls._PLUGIN_LOGGING = raw_config

    @classmethod
    def validate_config(cls, config: dict, default_level: str) -> None:
        """Validate and return a LoggingConfig object

        The plugin logging configuration validates that the handlers/loggers/formatters
        follow the supported loggers/formatters/handlers that beer-garden supports.

        :param config: A dictionary to validate
        :param default_level: A default level to use
        :return: A valid LoggingConfiguration object
        """
        if not config:
            raise LoggingLoadingError("No plugin logging configuration specified.")

        cls._validate_level(config.get("level", default_level))
        cls._validate_handlers(config.get("handlers", {}))
        cls._validate_formatters(config.get("formatters", {}))
        cls._validate_loggers(config.get("loggers", {}))

    @classmethod
    def _parse_python_logging_config(cls, python_logging_config, level):
        """Convert a python logging configuration into a plugin logging configuration.

        :param python_logging_config:
        :param level:
        :return:
        """
        cls.logger.debug(
            "Loading plugin logging configuration from python logger information "
            "specified in beer-garden"
        )
        default_level = python_logging_config.get("root", {}).get("level", level)

        handlers = cls._parse_python_handlers(
            python_logging_config.get("handlers"), level
        )
        formatters = cls._parse_python_formatters(
            python_logging_config.get("formatters")
        )
        loggers = {}

        return {
            "level": default_level,
            "loggers": loggers,
            "handlers": handlers,
            "formatters": formatters,
        }

    @classmethod
    def _parse_python_handlers(cls, handlers, level):
        """Convert python handlers into handlers that the plugins can understand.

        Namely, this takes a python configuration of handlers, inspects class
        names/handler names and returns only the ones that the bindings are responsible
        for implementing.

        :param handlers:
        :param level:
        :return:
        """
        handlers_to_return = {}
        for handler_name, handler_config in six.iteritems(handlers):
            if handler_name in LoggingConfig.SUPPORTED_HANDLERS:
                handlers_to_return[handler_name] = cls._parse_python_handler_config(
                    handler_config, level
                )
            elif handler_config.get("class") in cls.KNOWN_HANDLERS:
                standardized_name = cls._get_standardized_handler_name(
                    handler_config["class"]
                )
                handlers_to_return[
                    standardized_name
                ] = cls._parse_python_handler_config(handler_config, level)

        if not handlers_to_return:
            handlers_to_return["stdout"] = LoggingConfig.DEFAULT_HANDLER

        return handlers_to_return

    @staticmethod
    def _parse_python_formatters(formatters):
        """Convert python formatters into formatters that the plugins can understand.

        Namely, this takes a python configuration of formatters, inspects names
        and returns only the ones that the bindings are responsible for implementing.

        If it could not find any, it will always add a default formatter

        :param formatters:
        :return:
        """
        formatter_to_return = {"default": {"format": LoggingConfig.DEFAULT_FORMAT}}

        for formatter_name, formatter_info in six.iteritems(formatters):
            if formatter_name in LoggingConfig.SUPPORTED_HANDLERS:
                formatter_to_return[formatter_name] = copy.copy(formatter_info)

        return formatter_to_return

    @staticmethod
    def _parse_python_handler_config(handler_config, level):
        """Given a specific handler, will standardize the handler/formatter names

        :param handler_config:
        :param level:
        :return:
        """
        level = handler_config.get("level", level)
        formatter = handler_config.get("formatter")
        if formatter not in LoggingConfig.SUPPORTED_HANDLERS:
            formatter = "default"

        config_to_return = copy.copy(handler_config)
        config_to_return["level"] = level
        config_to_return["formatter"] = formatter
        return config_to_return

    @staticmethod
    def _validate_level(level: str):
        """Validate given level is in supported list.

        :param level:
        :return:
        """
        if level not in LoggingConfig.LEVELS:
            raise LoggingLoadingError(
                f"Invalid level '{level}', supported levels are {LoggingConfig.LEVELS}"
            )

    @classmethod
    def _validate_loggers(cls, loggers: dict) -> None:
        """Validate logger entry of a plugin logging configuration.

        Validates formatters/levels/handlers for all loggers given.

        :param loggers:
        :return:
        """
        for _logger_name, logger_info in six.iteritems(loggers):
            if logger_info.get("level"):
                cls._validate_level(logger_info.get("level"))

            if logger_info.get("handlers"):
                if isinstance(logger_info.get("handlers"), list):
                    for handler_name in logger_info.get("handlers"):
                        if handler_name not in LoggingConfig.SUPPORTED_HANDLERS:
                            raise LoggingLoadingError(
                                f"Invalid handler '{handler_name}', supported handlers are {LoggingConfig.SUPPORTED_HANDLERS}"
                            )
                else:
                    cls._validate_handlers(logger_info.get("handlers"))

            if logger_info.get("formatters"):
                cls._validate_formatters(logger_info.get("formatters"))

    @staticmethod
    def _validate_formatters(formatters: dict):
        """Validate that all formatters are supported.

        If no formatters are passed in, then the default formatter is returned.

        :param formatters:
        :return:
        """
        if not formatters:
            return {"default": {"format": LoggingConfig.DEFAULT_FORMAT}}

        for formatter_name, _formatter_info in six.iteritems(formatters):
            # TODO - WTF

            if formatter_name not in LoggingConfig.SUPPORTED_HANDLERS + ("default",):
                raise LoggingLoadingError(
                    "Invalid formatter specified (%s). Supported "
                    "formatters are: %s"
                    % (formatter_name, LoggingConfig.SUPPORTED_HANDLERS + ("default",))
                )

    @staticmethod
    def _validate_handlers(handlers: dict):
        """Validate that all handlers are supported.

        If no handlers are passed in, then the default handler is returned.

        :param handlers:
        :return:
        """
        if not handlers:
            return {"stdout": LoggingConfig.DEFAULT_HANDLER}

        for handler_name, _handler_config in six.iteritems(handlers):
            if handler_name not in LoggingConfig.SUPPORTED_HANDLERS:
                raise LoggingLoadingError(
                    f"Invalid handler '{handler_name}', supported handlers are {LoggingConfig.SUPPORTED_HANDLERS}"
                )

    @classmethod
    def _get_standardized_handler_name(cls, python_class):
        """Converts python-specific handlers into the correct handler label.

        :param python_class:
        :return:
        """
        if python_class in cls.STDOUT_HANDLERS:
            return "stdout"
        elif python_class in cls.FILE_HANDLERS:
            return "file"
        elif python_class in cls.LOGSTASH_HANDLERS:
            return "logstash"
        else:
            raise NotImplementedError(f"Invalid plugin log handler '{python_class}'")
