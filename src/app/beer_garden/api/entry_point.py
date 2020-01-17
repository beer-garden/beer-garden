# -*- coding: utf-8 -*-
import logging
import signal
from multiprocessing.context import BaseContext
from multiprocessing.queues import Queue
from types import FrameType
from typing import Any, Callable, TypeVar

from box import Box
from brewtils.models import Event

import beer_garden
import beer_garden.config
import beer_garden.db.api as db
import beer_garden.events.events_manager
import beer_garden.queue.api as queue
from beer_garden.events.processors import FanoutProcessor

T = TypeVar("T", bound="EntryPoint")


class EntryPoint(object):
    """A Beergarden API entry point

    This class represents an entry point into Beergarden.

    To create a new entry point:
    - Make a new subpackage under beer_garden.api
    - In that package's __init__ add a `run` function that will run the entry point
    process and a `signal_handler` function that will stop it
    - Add the new entry point to the configuration spec as a child of the "entry" dict.
    The name of the new dict must match the subpackage name, and the new entry must
    have an `enable` flag as an immediate child.

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
        downstream_queue: Queue,
    ):
        self._logger = logging.getLogger(__name__)
        self._name = name
        self._target = target
        self._signal_handler = signal_handler
        self._downstream_queue = downstream_queue
        self._process = None

    @classmethod
    def create(cls, module_name: str, downstream_queue: Queue) -> T:
        module = getattr(beer_garden.api, module_name)

        return EntryPoint(
            name=module_name,
            target=module.run,
            signal_handler=module.signal_handler,
            downstream_queue=downstream_queue,
        )

    def start(
        self, context: BaseContext, log_queue: Queue, events_queue: Queue
    ) -> None:
        """Start the entry point process

        Args:
            context: multiprocessing context to use when creating the process
            log_queue: queue to use for logging consolidation
            events_queue: queue to use to sent events to the main process

        Returns:
            None
        """
        process_name = f"BGEntryPoint-{self._name}"

        self._process = context.Process(
            target=self._target_wrapper,
            args=(
                beer_garden.config.get(),
                log_queue,
                events_queue,
                self._downstream_queue,
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
        self._process.terminate()
        self._process.join(timeout=timeout)

        if self._process.exitcode is None:
            self._logger.warning(
                f"Process {self._process.name} is still running - sending SIGKILL"
            )
            self._process.kill()

    def send_event(self, event: Event) -> None:
        """Send an event into the entry point process

        Args:
            event: The event to send

        Returns:
            None
        """
        self._downstream_queue.put(event)

    @staticmethod
    def _target_wrapper(
        config: Box,
        log_queue: Queue,
        event_queue: Queue,
        incoming_queue: Queue,
        target: Callable,
        signal_handler: Callable[[int, FrameType], None],
    ) -> Any:
        """Helper method that sets up the process environment before calling `target`

        This does several things that are needed by all entry points:
        - Sets up the signal handler function that will be used to terminate the process
        - Sets the global application configuration
        - Configures logging to send all records back to the main application process
        - Creates and registers a connection to the database

        It then calls the actual entry point target, which will be the `run` method in
        the subpackage's __init__.

        Args:
            config:
            log_queue:
            event_queue:
            incoming_queue:
            target:
            signal_handler:

        Returns:
            The result of the `target` function
        """
        # Set the process to ignore SIGINT and exit on SIGTERM
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal_handler)

        # First thing to do is set the config
        beer_garden.config.assign(config)

        # Then set up logging to push everything back to the main process
        beer_garden.log.setup_entry_point_logging(log_queue)

        # Also set up plugin logging
        beer_garden.log.load_plugin_log_config()

        # Set up a database connection
        db.create_connection(db_config=beer_garden.config.get("db"))

        # Set up message queue connections
        queue.create_clients(beer_garden.config.get("amq"))

        # Then setup upstream event queue (used to send events to the main process)
        beer_garden.events.events_manager.set_upstream(event_queue)

        # Start the event manager for incoming events (coming from the main process)
        event_manager = FanoutProcessor(name="EventManager", queue=incoming_queue)
        event_manager.start()

        # Now invoke the actual process target
        ret_val = target()

        # At this point we need to stop the event manager thread as well
        event_manager.stop()

        return ret_val
