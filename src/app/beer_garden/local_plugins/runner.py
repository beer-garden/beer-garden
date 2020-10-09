# -*- coding: utf-8 -*-

import logging
import subprocess
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Sequence

from time import sleep

from beer_garden.events.processors import LockListener

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
        error_log_lock: Lock,
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

        self.log_queue = Queue()
        self.error_log_lock = error_log_lock
        self.log_reader = LockListener(
            lock=self.error_log_lock,
            queue=self.log_queue,
            action=self._process_logs,
            name=f"{self} Log Processor",
        )

        self.error_log = self.process_cwd / "plugin.err"
        self.error_handler = logging.FileHandler(self.error_log)
        self.error_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Logger that will be used by the actual ProcessRunner
        self.logger = logging.getLogger(f"{__name__}.{self}")

        # Logger that will be used for captured STDOUT / STDERR
        self.capture_logger = logging.getLogger(f"runner.{self}")
        self.capture_logger.setLevel("DEBUG")

        Thread.__init__(self, name=self.runner_name)

    def __str__(self):
        return f"{self.runner_name}.{self.runner_id}"

    def associate(self, instance=None):
        """Associate this runner with a specific instance ID"""
        self.instance_id = instance.id

        # At this point we're satisfied that we won't need to write captured STDOUT /
        # STDERR to the error file so allow messages to be processed
        self.log_reader.start()

    def kill(self):
        """Kill the underlying plugin process with SIGKILL"""
        if self.process and self.process.poll() is None:
            self.logger.warning("About to kill process")
            self.process.kill()

    def run(self):
        """Runs the plugin process

        Run the plugin using the entry point specified with the generated environment in
        its own subprocess.
        """
        self.logger.info(f"Starting process with args {self.process_args}")

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
                target=self._read_stream,
                args=(self.process.stdout, logging.INFO),
                name=f"{self} STDOUT Reader",
            )
            stderr_thread = Thread(
                target=self._read_stream,
                args=(self.process.stderr, logging.ERROR),
                name=f"{self} STDERR Reader",
            )
            stdout_thread.start()
            stderr_thread.start()

            # Just spin here until until the process is no longer alive
            while self.process.poll() is None:
                sleep(0.1)

            self.logger.debug("About to join stream reader threads")
            stdout_thread.join()
            stderr_thread.join()

            # Ensure logs are sent SOMEWHERE in the event they were never configured
            # TODO - This is broken: QueueListener doesn't exhaust queue before dying
            if not self.log_reader.is_alive():
                self.logger.warning(
                    f"Plugin {self} terminated before successfully initializing. All "
                    f"captured messages will be written to {self.error_log} and the "
                    f"application logs."
                )

                # This is what enables logging to the error file
                self.capture_logger.addHandler(self.error_handler)

                self.log_reader.start()

                # Need to give the log_reader time to start, otherwise the stopped
                # check will happen before we start processing
                sleep(0.1)

            self.logger.debug("About to stop and join log processing thread")
            self.log_reader.stop()
            self.log_reader.join()

            self.logger.info("Plugin is officially stopped")

        except Exception as ex:
            self.logger.exception(f"Plugin died: {ex}")

    def _read_stream(self, stream, default_level):
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

                # TODO - timestamps are broken if we have to log everything at the end
                self.log_queue.put((level_to_log, line))

    def _process_logs(self, record):
        """Read messages off the logging queue and deal with them"""
        self.capture_logger.log(record[0], record[1])
