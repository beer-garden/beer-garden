import unittest
import copy
from mock import Mock, patch
from beer_garden.bg_utils.plugin_logging_loader import (
    PluginLoggingLoader,
    LoggingLoadingError,
)


class PluginLoggingLoaderTest(unittest.TestCase):

    loader = PluginLoggingLoader()

    def setUp(self):
        self.python_config = {
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "logstash": {"format": "%(message)s"},
            },
            "handlers": {
                "special-logstash": {
                    "level": "DEBUG",
                    "class": "logstash_async.handler.AsynchronousLogstashHandler",
                    "transport": "logstash_async.transport.TcpTransport",
                    "host": "localhost",
                    "port": 5000,
                    "ssl_enable": False,
                    "ssl_verify": False,
                    "ca_certs": None,
                    "certfile": None,
                    "keyfile": None,
                    "database_path": "test.sql",
                },
                "special-file": {
                    "backupCount": 20,
                    "class": "logging.handlers.RotatingFileHandler",
                    "encoding": "utf8",
                    "formatter": "default",
                    "level": "INFO",
                    "filename": "/path/to/filename",
                    "maxBytes": 10485760,
                },
                "brew-view": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "level": "INFO",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "tornado.access": {"level": "WARN"},
                "tornado.application": {"level": "WARN"},
                "tornado.general": {"level": "WARN"},
            },
            "root": {"handlers": ["brew-view"], "level": "INFO"},
            "version": 1,
        }
        self.config = {
            "level": "INFO",
            "handlers": {
                "logstash": {
                    "class": "logstash_async.handler.AsynchronousLogstashHandler",
                    "transport": "logstash_async.transport.TcpTransport",
                    "host": "localhost",
                    "port": 5000,
                    "ssl_enable": False,
                    "ssl_verify": False,
                    "ca_certs": None,
                    "certfile": None,
                    "keyfile": None,
                    "database_path": "test.sql",
                    "formatter": "default",
                },
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": "INFO",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "backupCount": 20,
                    "class": "logging.handlers.RotatingFileHandler",
                    "encoding": "utf8",
                    "formatter": "default",
                    "level": "INFO",
                    "maxBytes": 10485760,
                },
            },
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "logstash": {"format": "%(message)s"},
                "stdout": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
            },
            "loggers": {
                "plugin1": {
                    "level": "WARN",
                    "handlers": ["logstash", "stdout"],
                    "formatters": {"logstash": "%(ascitime)s - %(message)s"},
                },
                "plugin2": {"level": "DEBUG", "handlers": ["stdout"]},
                "plugin3": {"level": "INFO", "handlers": {"logstash": {"foo" "bar"}}},
            },
        }

    def test_load_no_file(self):
        config = self.loader.load(
            filename=None, level="INFO", default_config=self.python_config
        )
        self.assertEqual(config.level, "INFO")
        self.assertTrue("stdout" in config.handlers)
        self.assertTrue("logstash" in config.handlers)

    def test_load_no_file_verify_stdout(self):
        config = self.loader.load(
            filename=None, level="INFO", default_config=self.python_config
        )
        self.assertTrue("stdout" in config.handlers)
        stdout = config.handlers["stdout"]
        self.assertEqual(
            stdout,
            {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            },
        )

    def test_load_no_file_verify_logstash(self):
        config = self.loader.load(
            filename=None, level="INFO", default_config=self.python_config
        )
        self.assertTrue("logstash" in config.handlers)
        logstash = config.handlers["logstash"]
        self.assertEqual(
            logstash,
            {
                "level": "DEBUG",
                "class": "logstash_async.handler.AsynchronousLogstashHandler",
                "transport": "logstash_async.transport.TcpTransport",
                "host": "localhost",
                "port": 5000,
                "ssl_enable": False,
                "ssl_verify": False,
                "ca_certs": None,
                "certfile": None,
                "keyfile": None,
                "database_path": "test.sql",
                "formatter": "default",
            },
        )

    @patch("beer_garden.bg_utils.plugin_logging_loader.open")
    @patch("beer_garden.bg_utils.plugin_logging_loader.yaml")
    def test_setup_application_logging_from_file(self, yaml_mock, open_mock):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        fake_config = {"level": "DEBUG", "handlers": {}, "formatters": {}}
        yaml_mock.safe_load.return_value = fake_config
        config = self.loader.load(
            filename="fake_file", level="INFO", default_config=None
        )
        self.assertEqual(config.level, "DEBUG")

    def test_validate_config(self):
        config = self.loader.validate_config(self.config, "DEBUG")
        self.assertTrue("plugin1" in config._loggers)
        self.assertTrue("plugin2" in config._loggers)
        self.assertTrue("plugin3" in config._loggers)

    def test_validate_config_no_config(self):
        with self.assertRaises(LoggingLoadingError):
            self.loader.validate_config(None, "INFO")

    def test_invalid_level(self):
        with self.assertRaises(LoggingLoadingError):
            self.config["level"] = "INVALID"
            self.loader.validate_config(self.config, "INFO")

    def test_invalid_handler(self):
        with self.assertRaises(LoggingLoadingError):
            self.config["handlers"]["foo"] = "INVALID"
            self.loader.validate_config(self.config, "INFO")

    def test_invalid_formatter(self):
        with self.assertRaises(LoggingLoadingError):
            self.config["formatters"]["foo"] = "INVALID"
            self.loader.validate_config(self.config, "INFO")

    def test_invalid_logger_level(self):
        with self.assertRaises(LoggingLoadingError):
            self.config["loggers"]["plugin1"]["level"] = "INVALID"
            self.loader.validate_config(self.config, "INFO")

    def test_invalid_logger_handler_name(self):
        with self.assertRaises(LoggingLoadingError):
            self.config["loggers"]["plugin1"]["handlers"].append("INVALID")
            self.loader.validate_config(self.config, "INFO")

    def test_invalid_logger_formatter(self):
        with self.assertRaises(LoggingLoadingError):
            self.config["loggers"]["plugin1"]["formatters"]["INVALID"] = {}
            self.loader.validate_config(self.config, "INFO")

    def test_load_handler_name_match(self):
        logstash_config = copy.copy(self.python_config["handlers"]["special-logstash"])
        del self.python_config["handlers"]["special-logstash"]
        self.python_config["handlers"]["logstash"] = logstash_config
        config = self.loader.load(None, "INFO", self.python_config)
        self.assertTrue("logstash" in config.handlers)
        logstash = config.handlers["logstash"]
        self.assertEqual(
            logstash,
            {
                "level": "DEBUG",
                "class": "logstash_async.handler.AsynchronousLogstashHandler",
                "transport": "logstash_async.transport.TcpTransport",
                "host": "localhost",
                "port": 5000,
                "ssl_enable": False,
                "ssl_verify": False,
                "ca_certs": None,
                "certfile": None,
                "keyfile": None,
                "database_path": "test.sql",
                "formatter": "default",
            },
        )

    def test_load_default_handler(self):
        self.python_config["handlers"] = {}
        config = self.loader.load(None, "INFO", self.python_config)
        self.assertTrue("stdout" in config.handlers)


if __name__ == "__main__":
    unittest.main()
