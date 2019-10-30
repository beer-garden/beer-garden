# -*- coding: utf-8 -*-
import logging
import signal
from multiprocessing.context import BaseContext
from multiprocessing.queues import Queue
from types import FrameType
from typing import Any, Callable, TypeVar

from box import Box

import beer_garden.config
import beer_garden.db.api as db

T = TypeVar("T", bound="EntryPoint")


class EntryPoint(object):
    """A Beergarden API entry point

    This class represents an entry point into Beergarden.

    Args:
        name: Part of the process name. Full name will be "BGEntryPoint-{name}"
        target: The method that will be called when the process starts
        signal_handler: SIGTERM handler to gracefully shut down the process

    """

    def __init__(
        self,
        name: str,
        target: Callable,
        signal_handler: Callable[[int, FrameType], None],
    ):
        self._logger = logging.getLogger(__name__)
        self._name = name
        self._target = target
        self._signal_handler = signal_handler
        self._process = None

    @classmethod
    def create(cls, module_name: str) -> T:
        module = getattr(beer_garden.api, module_name)
        return EntryPoint(module_name, module.run, signal_handler=module.signal_handler)

    def start(self, context: BaseContext, log_queue: Queue) -> None:
        """Start the entry point process

        Args:
            context: multiprocessing context to use when creating the process
            log_queue: queue to use for logging consolidation

        Returns:
            None
        """
        process_name = f"BGEntryPoint-{self._name}"

        self._process = context.Process(
            target=self._target_wrapper,
            args=(
                beer_garden.config.get(),
                log_queue,
                self._target,
                self._signal_handler,
            ),
            name=process_name,
            daemon=True,
        )
        self._process.start()

    def stop(self, timeout: int = None) -> None:
        """Stop the process with a SIGTERM

        If a `timeout` is specified this method will wait that long for the process to
        stop gracefully. If the process has still not stopped after the timeout expires
        it will be forcefully terminated with SIGKILL.

        Args:
            timeout: Amount of time to wait for the process to stop

        Returns:
            None
        """
        # TODO - Should we start with INT?
        self._process.terminate()
        self._process.join(timeout=timeout)

        if self._process.exitcode is None:
            self._logger.warning(
                f"Process {self._process.name} is still running - sending SIGKILL"
            )
            self._process.kill()

    @staticmethod
    def _target_wrapper(
        config: Box,
        log_queue: Queue,
        target: Callable,
        signal_handler: Callable[[int, FrameType], None],
    ) -> Any:
        """Helper method that sets up the process environment before calling `target`

        Args:
            config:
            log_queue:
            target:
            signal_handler:

        Returns:
            The result of the `target` function
        """
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Absolute first thing to do is set the config
        beer_garden.config.assign(config)

        # Then set up logging to push everything back to the main process
        beer_garden.log.setup_entry_point_logging(log_queue)

        # Set up a database connection
        db.create_connection(db_config=beer_garden.config.get("db"))

        # Now invoke the actual process target
        return target()
