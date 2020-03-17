# -*- coding: utf-8 -*-

import logging
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from threading import Event, Thread
from time import sleep
from typing import Sequence

import beer_garden.config as config
from beer_garden.events.processors import DelayListener

log_levels = [n for n in getattr(logging, "_nameToLevel").keys()]


class ProcessRunner(Thread):
    """Thread that 'manages' a Plugin process.

    A runner will take care of creating and starting a process that will run the
    plugin entry point.

    Logging here is kind of wonky. I want to get to the point where the brewtils.Plugin
    asks Beer-garden for a configuration by default - that would allow the plugin
    processes to log directly to the correct files instead of reading STDOUT / STDERR
    constantly. Alas, we aren't there yet.

    Until then - this is how that logging works:
    - logger is the normal python logger for this class
    - plugin_logger is the logger used to log records coming from the plugin process

    There's a bit of a chicken vs egg issue with regards to configuring logging. At
    *runner* creation time we may or may not know the system name / version / instance
    since the only thing *required* in the beer.conf is the entry point. This is a
    problem because we need that info in order to name the log file correctly.

    So we essentially punt on assigning a handler to the plugin_logger until the
    Plugin actually registers. Everything read from the process gets placed into a
    queue, and the queue won't be processed until ``associate`` is called. At that point
    we'll have all the info necessary to create and assign a handler and we'll begin
    processing the queue.

    In the event that the Plugin process doesn't register successfully we'll dump the
    queued records to the "normal" log. This is really all we can do - they need to go
    *somewhere* and that's really the only sensible place.

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
        self.logger = logging.getLogger(f"{__name__}.{self.runner_name}")

        self.log_queue = Queue()
        self.logger_ready = Event()
        self.process_logger = self._get_logger()
        self._set_handler()

        Thread.__init__(self, name=self.runner_name)

    def associate(self, system=None, instance=None):
        """Associate this runner with a specific System and Instance

        Right now the only thing this does is configure logging if not already done.
        """
        if not self.logger_ready.is_set():
            self._set_handler(system=system, instance=instance)

    def kill(self):
        """Kill the underlying plugin process with SIGKILL"""
        if self.process and self.process.poll() is None:
            self.logger.warning(f"About to kill process")
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
                target=self._read_stream, args=(self.process.stdout, logging.INFO),
            )
            stderr_thread = Thread(
                target=self._read_stream, args=(self.process.stderr, logging.ERROR),
            )
            stdout_thread.start()
            stderr_thread.start()

            # Processing the logs also needs a thread
            log_reader = DelayListener(
                event=self.logger_ready, queue=self.log_queue, action=self._process_logs
            )
            log_reader.start()

            # Just spin here until until the process is no longer alive
            while self.process.poll() is None:
                sleep(0.1)

            self.logger.debug(f"About to join stream reader threads")
            stdout_thread.join()
            stderr_thread.join()

            # Ensure logs are sent SOMEWHERE in the event they were never configured
            # TODO - This is broken: QueueListener doesn't exhaust queue before dying
            if not self.logger_ready.is_set():
                self.logger.warning(
                    f"Logger for plugin {self.runner_name} was never started. About to "
                    f"log all queued log records using Beer-garden logging config"
                )

                self.process_logger = self.logger
                self.logger_ready.set()

                # Need to give the log_reader time to start, otherwise the stopped
                # check will happen before we start processing
                sleep(0.1)

            self.logger.debug(f"About to stop and join log processing thread")
            log_reader.stop()
            log_reader.join()

            self.logger.info(f"Plugin is officially stopped")

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

    def _get_logger(self):
        log_level = "INFO"

        logger = logging.getLogger(f"{self.runner_id}")
        logger.propagate = False
        logger.setLevel(log_level)

        # if log_level is None:
        #     log_level = logging.getLogger(__name__).getEffectiveLevel()

        # if len(log.handlers) > 0:
        #     return log

        return logger

    def _set_handler(self, system=None, instance=None):
        handler = None
        log_level = "INFO"
        format_string = None
        log_directory = config.get("plugin.local.log_directory")

        if not log_directory:
            handler = logging.StreamHandler(sys.stdout)
        elif system and instance:
            base_dir = Path(config.get("plugin.local.log_directory"))

            log_dir = base_dir / system.namespace / system.name / system.version
            log_dir.mkdir(exist_ok=True, parents=True)

            handler = RotatingFileHandler(
                log_dir / f"{instance.name}.log", backupCount=5, maxBytes=10485760
            )

        if handler:
            handler.setLevel(log_level)
            handler.setFormatter(logging.Formatter(format_string))

            self.process_logger.addHandler(handler)
            self.logger_ready.set()

    def _process_logs(self, record):
        """Read messages off the logging queue and deal with them"""
        self.process_logger.log(record[0], record[1])
