# -*- coding: utf-8 -*-

import logging
import subprocess
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Sequence


class ProcessRunner(Thread):
    """Thread that 'manages' a Plugin process.

    A runner will take care of creating and starting a process that will run the
    plugin entry point.

    """

    def __init__(
        self,
        runner_id: str,
        process_args: Sequence[str],
        process_cwd: Path,
        process_env: dict,
    ):
        self.runner_id = runner_id
        self.process_args = process_args
        self.process_cwd = process_cwd
        self.process_env = process_env

        self.process = None
        self.runner_name = process_cwd.name
        self.logger = logging.getLogger(f"{__name__}.{self.runner_name}")

        Thread.__init__(self, name=self.runner_id)

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
            )

            # Just spin here until until the process is no longer alive
            while self.process.poll() is None:
                sleep(0.1)

            self.logger.info(f"Plugin is officially stopped")

        except Exception as ex:
            self.logger.exception(f"Plugin died: {ex}")
