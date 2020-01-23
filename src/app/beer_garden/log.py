# -*- coding: utf-8 -*-
import copy
import logging
import logging.config
import logging.handlers

import six
from brewtils.models import LoggingConfig
from ruamel import yaml
from ruamel.yaml import YAML

import beer_garden
from beer_garden.errors import LoggingLoadingError

plugin_logging_config = None
_LOGGING_CONFIG = None


def load(config: dict, force=False) -> None:
    """Load the application logging configuration.

    Will attempt to use a file specified by the log_config_file config item. If that
    item resolves to None then will use the "default" logging configuration with the
    values from the log_level and log_file configuration items.

    Args:
        config: Subsection "log" of the loaded configuration
        force: Force a reload.
    """
    global _LOGGING_CONFIG
    if _LOGGING_CONFIG is not None and not force:
        return

    logging_filename = config.get("config_file")

    if logging_filename:
        with open(logging_filename, "rt") as log_file:
            logging_config = YAML().load(log_file)
    else:
        logging_config = default_app_config(config.get("level"), config.get("file"))

    logging.config.dictConfig(logging_config)

    _LOGGING_CONFIG = logging_config


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
    root = logging.getLogger()
    root.addHandler(logging.handlers.QueueHandler(queue))
    root.setLevel(logging.DEBUG)


def get_plugin_log_config(system_name=None):
    return plugin_logging_config.get_plugin_log_config(system_name=system_name)


def load_plugin_log_config():
    global plugin_logging_config

    plugin_config = beer_garden.config.get("plugin")
    plugin_logging_config = PluginLoggingLoader.load(
        filename=plugin_config.logging.config_file,
        level=plugin_config.logging.level,
        default_config=_LOGGING_CONFIG,
    )


def reload_plugin_log_config():
    load_plugin_log_config()

    return get_plugin_log_config()


class PluginLoggingLoader(object):
    """A class for loading plugin logging configuration from files.

    Usually used by simply calling `load`. If given a filename, it will attempt to pull
    a valid logging configuration object from the file given. If no file was given, it
    will fall-back to the default configuration. This is assumed to be a valid python
    logging configuration dict (i.e. something you would pass to `logging.dictConfig`).

    """

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
    def load(cls, filename, level, default_config):
        """Load a LoggingConfig

        If no filename is given, will fallback to the default config passed in.

        :param filename: Filename of the plugin logging configuration to load
        :param level: A default level for the loggers
        :param default_config: A default configuration to fallback on if no plugin log
        is present
        :return: A valid LoggingConfig object
        """
        config = {}

        if filename:
            with open(filename) as log_config_file:
                config = yaml.safe_load(log_config_file)

        # If no config could be found from a file use the default
        if not config:
            config = cls._parse_python_logging_config(default_config, level)

        valid_config = cls.validate_config(config, level)

        return valid_config

    @classmethod
    def validate_config(cls, config_to_validate, level):
        """Validate and return a LoggingConfig object

        The plugin logging configuration validates that the handlers/loggers/formatters
        follow the supported loggers/formatters/handlers that beer-garden supports.

        :param config_to_validate: A dictionary to validate
        :param level: A default level to use
        :return: A valid LoggingConfiguration object
        """
        if not config_to_validate:
            raise LoggingLoadingError("No plugin logging configuration specified.")

        default_level = cls._validate_level(config_to_validate.get("level", level))
        cls.logger.debug("Default level: %s" % default_level)

        handlers = cls._validate_handlers(config_to_validate.get("handlers", {}))
        formatters = cls._validate_formatters(config_to_validate.get("formatters", {}))
        loggers = cls._validate_loggers(config_to_validate.get("loggers", {}))

        return LoggingConfig(
            level=default_level,
            handlers=handlers,
            formatters=formatters,
            loggers=loggers,
        )

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

    @classmethod
    def _validate_loggers(cls, loggers):
        """Validate logger entry of a plugin logging configuration.

        Validates formatters/levels/handlers for all loggers given.

        :param loggers:
        :return:
        """
        for logger_name, logger_info in six.iteritems(loggers):
            if logger_info.get("level"):
                cls._validate_level(logger_info.get("level"))

            if logger_info.get("handlers"):
                if isinstance(logger_info.get("handlers"), list):
                    for handler_name in logger_info.get("handlers"):
                        if handler_name not in LoggingConfig.SUPPORTED_HANDLERS:
                            raise LoggingLoadingError(
                                "Invalid handler specified (%s). Supported handlers are: %s"
                                % (handler_name, LoggingConfig.SUPPORTED_HANDLERS)
                            )
                else:
                    cls._validate_handlers(logger_info.get("handlers"))

            if logger_info.get("formatters"):
                cls._validate_formatters(logger_info.get("formatters"))

        return loggers

    @staticmethod
    def _validate_formatters(formatters):
        """Validate that all formatters are supported.

        If no formatters are passed in, then the default formatter is returned.

        :param formatters:
        :return:
        """
        if not formatters:
            return {"default": {"format": LoggingConfig.DEFAULT_FORMAT}}

        for formatter_name, formatter_info in six.iteritems(formatters):

            if formatter_name not in LoggingConfig.SUPPORTED_HANDLERS + ("default",):
                raise LoggingLoadingError(
                    "Invalid formatters specified (%s). Supported "
                    "formatters are: %s"
                    % (formatter_name, LoggingConfig.SUPPORTED_HANDLERS + ("default",))
                )

        return formatters

    @staticmethod
    def _validate_handlers(handlers):
        """Validate that all handlers are supported.

        If no handlers are passed in, then the default handler is returned.

        :param handlers:
        :return:
        """
        if not handlers:
            return {"stdout": LoggingConfig.DEFAULT_HANDLER}

        for handler_name, handler_config in six.iteritems(handlers):
            if handler_name not in LoggingConfig.SUPPORTED_HANDLERS:
                raise LoggingLoadingError(
                    "Invalid handler specified (%s). "
                    "Supported handlers are: %s"
                    % (handler_name, LoggingConfig.SUPPORTED_HANDLERS)
                )

        return handlers

    @staticmethod
    def _validate_level(level):
        """Validate given level is in supported list.

        :param level:
        :return:
        """
        if level not in LoggingConfig.LEVELS:
            raise LoggingLoadingError(
                f"Invalid level '{level}', supported levels are {LoggingConfig.LEVELS}"
            )
        return level

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
            raise NotImplementedError("Invalid plugin log handler (%s)" % python_class)
