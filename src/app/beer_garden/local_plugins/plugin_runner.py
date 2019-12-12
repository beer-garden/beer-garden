# -*- coding: utf-8 -*-

import logging
import subprocess
import sys
from pathlib import Path
from threading import Thread
from time import sleep

from brewtils.models import System
from brewtils.stoppable_thread import StoppableThread

from beer_garden.local_plugins.logger import getLogLevels, getPluginLogger


class PluginRunner(StoppableThread):
    """Thread that 'manages' a Plugin process.

    A runner will take care of creating and starting a process that will run the
    plugin entry point. It will then monitor that process's STDOUT and STDERR and will
    log anything it sees.

    """

    def __init__(
        self,
        entry_point,
        system: System,
        instance_name: str,
        working_dir: Path,
        environment: dict,
        plugin_log_directory=None,
        **kwargs
    ):
        self.entry_point = entry_point
        self.system = system
        self.instance_name = instance_name
        self.working_dir = working_dir
        self.environment = environment

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

        if kwargs.get("plugin_args"):
            self.executable += kwargs.get("plugin_args")

        self.unique_name = "%s[%s]-%s" % (
            self.system.name,
            self.instance_name,
            self.system.version,
        )

        self.log_levels = getLogLevels()

        log_config = {
            "log_directory": plugin_log_directory,
            "log_name": self.unique_name,
        }

        # Logger used for beer_garden purposes.
        self.logger = getPluginLogger(
            self.unique_name,
            format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            **log_config
        )

        log_config["log_level"] = kwargs.get("log_level", logging.INFO)
        self.unformatted_logger = getPluginLogger(
            self.unique_name + "-uf", **log_config
        )

        StoppableThread.__init__(self, logger=self.logger, name=self.unique_name)

    def kill(self):
        """Kills the plugin by killing the underlying process."""
        if self.process and self.process.poll() is None:
            self.logger.warning("About to kill plugin %s", self.unique_name)
            self.process.kill()
            self.logger.warning("Plugin %s has been killed", self.unique_name)

    def run(self):
        """Runs the plugin

        Run the plugin using the entry point specified with the generated environment in
        its own subprocess. Pipes STDOUT and STDERR such that when the plugin stops
        executing (or IO is flushed) it will log it.
        """
        try:
            self.logger.info(
                "Starting plugin %s subprocess: %s", self.unique_name, self.executable
            )
            self.process = subprocess.Popen(
                args=self.executable,
                env=self.environment,
                cwd=str(self.working_dir.resolve()),
                start_new_session=True,
                close_fds=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
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

        If we can't determine the log level then we'll log the message at
        ``default_level``. That way we guarantee messages are outputted (this
        is usually caused by a plugin writing to STDOUT / STDERR directly or
        raising an exception with a stacktrace).
        """
        stream_reader = iter(stream.readline, "")

        for raw_line in stream_reader:
            line = raw_line.rstrip()

            level_to_log = default_level
            for level in self.log_levels:
                if line.find(level) != -1:
                    level_to_log = getattr(logging, level)
                    break

            self.unformatted_logger.log(level_to_log, line)

        if self.process.poll() is None:
            self.logger.debug("Process isn't quite dead yet, reading IO again")
            self._check_io(stream, default_level)
