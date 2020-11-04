# -*- coding: utf-8 -*-
import logging
import os
import signal
import subprocess
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Dict, Sequence

import beer_garden.config as config

log_levels = [n for n in getattr(logging, "_nameToLevel").keys()]


class ProcessRunner(Thread):
    """Thread that 'manages' a Plugin process.

    A runner will take care of creating and starting a process that will run the
    plugin entry point.

    Logging here is a little interesting. We expect that plugins will be created as the
    first order of business in the plugin's ``main()``. Part of the Plugin initialize
    is asking beer-garden for a logging configuration, so anything after that point will
    be handled according to the returned configuration.

    However, there are two potential problems: the plugin may have logging calls before
    initializing the Plugin (even though it's not recommended), and the Plugin may fail
    to register at all for whatever reason.

    Both of these cases are handled the same way. We read STDOUT and STDERR from the
    process, and everything gets placed into a queue. The queue won't be processed until
    one of two things happen:
        - The ``associate`` method is called. This means that the plugin has
        successfully registered
        - The plugin process dies

    Once either of those happen we check to see if there are any items on the logging
    queue. If so, we prepend a message saying what's about to happen, and then we log
    all messages. Messages will be logged according to the normal application config
    as well as a special error file in the plugin log directory. This error file will
    be overwritten every time the plugin is run.

    Two support this slightly odd setup this class has two loggers:
    - logger is the normal python logger for this class
    - capture_logger is the logger used to log records coming from the plugin process

    """

    def __init__(
        self,
        runner_id: str,
        process_args: Sequence[str],
        process_cwd: Path,
        process_env: dict,
    ):
        self.process = None
        self.restart = False
        self.stopped = False
        self.dead = False

        self.runner_id = runner_id
        self.instance_id = ""

        self.process_args = process_args
        self.process_cwd = process_cwd
        self.process_env = process_env
        self.runner_name = process_cwd.name

        # Logger that will be used by the actual ProcessRunner
        self.logger = logging.getLogger(f"{__name__}.{self}")

        # Loggers that will be used for captured STDOUT / STDERR
        self.stdout_logger = logging.getLogger(f"runner.{self}.stdout")
        self.stdout_logger.setLevel("DEBUG")
        self.stderr_logger = logging.getLogger(f"runner.{self}.stderr")
        self.stderr_logger.setLevel("DEBUG")

        if config.get("plugin.local.logging.stream_files"):
            # This is kind of gross. We want to use the same formatting as the
            # application logging but Python doesn't make this easy. Formatters don't
            # have their own existence, they're just an attribute of a Handler. So
            # if there are any file-type handlers configured use the formatter
            # for that one, otherwise just use the first handler's formatter.
            root_logger = logging.getLogger("")
            handler = root_logger.handlers[0]
            for h in root_logger.handlers:
                if isinstance(h, logging.FileHandler):
                    handler = h
                    break

            stdout_handler = logging.FileHandler(self.process_cwd / "plugin.out")
            stdout_handler.setFormatter(handler.formatter)
            self.stdout_logger.addHandler(stdout_handler)

            stderr_handler = logging.FileHandler(self.process_cwd / "plugin.err")
            stdout_handler.setFormatter(handler.formatter)
            self.stderr_logger.addHandler(stderr_handler)

        Thread.__init__(self, name=self.runner_name)

    def __str__(self):
        return f"{self.runner_name}.{self.runner_id}"

    def state(self) -> Dict:
        """Pickleable representation"""

        return {
            "runner_name": self.runner_name,
            "runner_id": self.runner_id,
            "instance_id": self.instance_id,
            "restart": self.restart,
            "stopped": self.stopped,
            "dead": self.dead,
        }

    def associate(self, instance=None):
        """Associate this runner with a specific instance ID"""
        self.instance_id = instance.id

    def terminate(self):
        """Kill the underlying plugin process with SIGTERM"""
        if self.process and self.process.poll() is None:
            self.logger.debug("About to send SIGINT")
            os.kill(self.process.pid(), signal.SIGINT)

    def kill(self):
        """Kill the underlying plugin process with SIGKILL"""
        if self.process and self.process.poll() is None:
            self.logger.warning("About to send SIGKILL")
            self.process.kill()

    def run(self):
        """Runs the plugin process

        Run the plugin using the entry point specified with the generated environment in
        its own subprocess.
        """
        self.logger.debug(f"Starting process with args {self.process_args}")

        try:
            self.process = subprocess.Popen(
                args=self.process_args,
                env=self.process_env,
                cwd=str(self.process_cwd.resolve()),
                restore_signals=False,
                close_fds=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Reading process IO is blocking so needs to be in separate threads
            stdout_thread = Thread(
                name=f"{self} STDOUT Reader",
                target=self._read_stream,
                args=(self.process.stdout, logging.INFO, self.stdout_logger),
            )
            stderr_thread = Thread(
                name=f"{self} STDERR Reader",
                target=self._read_stream,
                args=(self.process.stderr, logging.ERROR, self.stderr_logger),
            )
            stdout_thread.start()
            stderr_thread.start()

            # Just spin here until until the process is no longer alive
            while self.process.poll() is None:
                sleep(0.1)

            self.logger.debug("About to join stream reader threads")
            stdout_thread.join()
            stderr_thread.join()

            if not self.instance_id:
                self.logger.warning(
                    f"Plugin {self} terminated before successfully initializing."
                )

            self.logger.debug("Plugin is officially stopped")

        except Exception as ex:
            self.logger.exception(f"Plugin died: {ex}")

    def _read_stream(self, stream, default_level, logger):
        """Helper function thread target to read IO from the plugin's subprocess

        This will read line by line from STDOUT or STDERR. If the line includes one of
        the log levels that the python logger knows about it will be logged at that
        level, otherwise it will be logged at the default level for that stream. For
        STDOUT this is INFO and for STDERR this is ERROR.

        That way we guarantee messages are outputted (this is usually caused by a plugin
         writing to STDOUT / STDERR directly or raising an exception with a stacktrace).
        """
        stream_reader = iter(stream.readline, "")

        # Sometimes the iter can finish before the process is really done
        while self.process.poll() is None:
            for raw_line in stream_reader:
                line = raw_line.rstrip()

                level_to_log = default_level
                for level in log_levels:
                    if line.find(level) != -1:
                        level_to_log = getattr(logging, level)
                        break

                logger.log(level_to_log, line)
