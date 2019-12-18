# -*- coding: utf-8 -*-

import logging
import subprocess
from pathlib import Path
from typing import Sequence

from brewtils.stoppable_thread import StoppableThread
from time import sleep


class PluginRunner(StoppableThread):
    """Thread that 'manages' a Plugin process.

    A runner will take care of creating and starting a process that will run the
    plugin entry point. It will then monitor that process's STDOUT and STDERR and will
    log anything it sees.

    """

    def __init__(
        self,
        unique_name: str,
        process_args: Sequence[str],
        process_cwd: Path,
        process_env: dict,
    ):
        self.logger = logging.getLogger(__name__)
        self.unique_name = unique_name

        self.process_args = process_args
        self.process_cwd = process_cwd
        self.process_env = process_env
        self.process = None

        StoppableThread.__init__(self, logger=self.logger, name=self.unique_name)

    def kill(self):
        """Kills the plugin by killing the underlying process."""
        if self.process and self.process.poll() is None:
            self.logger.warning(f"About to kill plugin {self.unique_name}")
            self.process.kill()

    def run(self):
        """Runs the plugin

        Run the plugin using the entry point specified with the generated environment in
        its own subprocess. Pipes STDOUT and STDERR such that when the plugin stops
        executing (or IO is flushed) it will log it.
        """
        self.logger.info(f"Starting plugin {self.unique_name}: {self.process_args}")

        try:
            self.process = subprocess.Popen(
                args=self.process_args,
                env=self.process_env,
                cwd=str(self.process_cwd.resolve()),
                start_new_session=True,
                close_fds=True,
                universal_newlines=True,
                bufsize=1,
            )

            # Just spin here until until the process is no longer alive
            while self.process.poll() is None:
                sleep(0.1)

            # If stopped wasn't set then this was not expected
            if not self.stopped():
                self.logger.error(f"Plugin {self.unique_name} unexpectedly shutdown!")

            self.logger.info(f"Plugin {self.unique_name} is officially stopped")

        except Exception as ex:
            self.logger.exception(f"Plugin {self.unique_name} died: {ex}")
