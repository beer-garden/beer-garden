import logging
import os
import sys
from threading import Thread
from time import sleep
import signal

from bartender.local_plugins.env_help import expand_string_with_environment_var
from mongoengine import DoesNotExist, OperationError

from bartender.local_plugins.logger import getLogLevels, getPluginLogger
from brewtils.stoppable_thread import StoppableThread

# This is the recommended import pattern, see https://github.com/google/python-subprocess32
if os.name == "posix" and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess


class LocalPluginRunner(StoppableThread):
    """Class for running a local plugin in its own process.

    Can be stopped/started and killed like a normal process"""

    def __init__(
        self,
        entry_point,
        system,
        instance_name,
        path_to_plugin,
        web_host,
        web_port,
        ssl_enabled,
        plugin_args=None,
        environment=None,
        requirements=None,
        plugin_log_directory=None,
        url_prefix=None,
        ca_verify=True,
        ca_cert=None,
        **kwargs
    ):
        self.entry_point = entry_point
        self.system = system
        self.instance_name = instance_name
        self.path_to_plugin = path_to_plugin
        self.web_host = web_host
        self.web_port = web_port
        self.ssl_enabled = ssl_enabled
        self.plugin_args = plugin_args or []
        self.environment = environment or {}
        self.requirements = requirements or []
        self.plugin_log_directory = plugin_log_directory
        self.url_prefix = url_prefix
        self.ca_verify = ca_verify
        self.ca_cert = ca_cert
        self.username = kwargs.get("username", None)
        self.password = kwargs.get("password", None)
        self.plugin_default_log_level = kwargs.get("log_level", logging.INFO)

        for instance in self.system.instances:
            if instance.name == self.instance_name:
                self.instance = instance
                break

        self.process = None
        self.executable = [sys.executable]
        if self.entry_point.startswith("-m "):
            self.executable.append("-m")
            self.executable.append(self.entry_point.split(" ", 1)[1])
        else:
            self.executable.append(self.entry_point)
        self.executable += self.plugin_args

        self.unique_name = "%s[%s]-%s" % (
            self.system.name,
            self.instance_name,
            self.system.version,
        )

        self.log_levels = getLogLevels()
        log_config = {
            "log_directory": self.plugin_log_directory,
            "log_name": self.unique_name,
        }

        # Logger used for bartender purposes.
        self.logger = getPluginLogger(
            self.unique_name,
            format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            **log_config
        )

        log_config["log_level"] = self.plugin_default_log_level
        self.unformatted_logger = getPluginLogger(
            self.unique_name + "-uf", **log_config
        )
        self.timestamp_logger = getPluginLogger(
            self.unique_name + "-ts",
            format_string="%(asctime)s - %(message)s",
            **log_config
        )

        StoppableThread.__init__(self, logger=self.logger, name=self.unique_name)

    @property
    def status(self):
        try:
            # TODO: Remove this reload. We have to find a better way to store the status
            # that doesn't require a database connection.
            self.instance.reload()
            return self.instance.status
        except (DoesNotExist, OperationError):
            self.logger.error("Error getting status of plugin %s" % self.unique_name)
            return "UNKNOWN"

    @status.setter
    def status(self, value):
        try:
            # TODO: Remove this reload. We have to find a better way to store the status
            # that doesn't require a database connection.
            self.instance.reload()
            self.instance.status = value
            self.instance.save()
        except (DoesNotExist, OperationError):
            self.logger.error(
                "Error updating status of plugin %s to %s" % (self.unique_name, value)
            )

    def kill(self):
        """Kills the plugin by killing the underlying process."""
        if self.process and self.process.poll() is None:
            self.logger.warning("About to kill plugin %s", self.unique_name)
            self.process.kill()
            self.logger.warning("Plugin %s has been killed", self.unique_name)

    def run(self):
        """Runs the plugin

        Run the plugin using the entry point specified with the generated environment in its own
        subprocess. Pipes STDOUT and STDERR such that when the plugin stops executing
        (or IO is flushed) it will log it.
        """
        try:
            self.logger.info(
                "Starting plugin %s subprocess: %s", self.unique_name, self.executable
            )
            self.process = subprocess.Popen(
                self.executable,
                bufsize=0,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=self._generate_plugin_environment(),
                cwd=os.path.abspath(self.path_to_plugin),
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
            )

            # Reading the process IO is blocking and we need to shutdown
            # gracefully, so reading IO needs to be its own thread
            stdout_thread = Thread(
                target=self._check_io,
                name=self.unique_name + "_stdout_thread",
                args=(self.process.stdout, logging.INFO),
            )
            stderr_thread = Thread(
                target=self._check_io,
                name=self.unique_name + "_stderr_thread",
                args=(self.process.stderr, logging.ERROR),
            )
            stdout_thread.start()
            stderr_thread.start()

            # Just spin here until until the process is no longer alive
            while self.process.poll() is None:
                sleep(0.1)

            self.logger.info(
                "Plugin %s subprocess has stopped with exit status %s, "
                "performing final IO read(s)",
                self.unique_name,
                self.process.poll(),
            )
            stdout_thread.join()
            stderr_thread.join()

            # If stopped wasn't set then this was not expected
            if not self.stopped():
                self.logger.error("Plugin %s unexpectedly shutdown!", self.unique_name)

            self.logger.info("Plugin %s is officially stopped", self.unique_name)

        except Exception as ex:
            self.logger.error("Plugin %s died", self.unique_name)
            self.logger.error(str(ex))

    def _check_io(self, stream, default_level):
        """Helper function thread target to read IO from the plugin's subprocess

        This will read line by line from STDOUT or STDERR. If the line includes
        one of the log levels that the python logger knows about we assume that
        the plugin has its own logger and formatter. In that case we log to our
        unformatted logger at the same level to keep the original formatting.

        If we can't determine the log level then we'll add a timestamp to the
        start and log the message at ``default_level``. That way we guarantee
        messages are outputted (this is usually caused by a plugin writing to
        STDOUT / STDERR directly or raising an exception with a stacktrace).
        """
        stream_reader = iter(stream.readline, "")

        for raw_line in stream_reader:
            line = raw_line.rstrip()

            level_to_log = None
            for level in self.log_levels:
                if line.find(level) != -1:
                    level_to_log = getattr(logging, level)
                    break

            if level_to_log:
                self.unformatted_logger.log(level_to_log, line)
            else:
                self.timestamp_logger.log(default_level, line)

        if self.process.poll() is None:
            self.logger.debug("Process isn't quite dead yet, reading IO again")
            self._check_io(stream, default_level)

    def _generate_plugin_environment(self):

        plugin_env = {
            "BG_NAME": self.system.name,
            "BG_VERSION": self.system.version,
            "BG_INSTANCE_NAME": self.instance_name,
            "BG_PLUGIN_PATH": self.path_to_plugin,
            "BG_WEB_HOST": self.web_host,
            "BG_WEB_PORT": self.web_port,
            "BG_SSL_ENABLED": self.ssl_enabled,
            "BG_URL_PREFIX": self.url_prefix,
            "BG_CA_VERIFY": self.ca_verify,
            "BG_CA_CERT": self.ca_cert,
            "BG_USERNAME": self.username,
            "BG_PASSWORD": self.password,
            "BG_LOG_LEVEL": logging.getLevelName(self.plugin_default_log_level),
        }

        for key, value in plugin_env.items():
            plugin_env[key] = str(value)

        for key, value in self.environment.items():
            plugin_env[key] = expand_string_with_environment_var(str(value), plugin_env)

        return plugin_env
