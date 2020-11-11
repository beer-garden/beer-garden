# -*- coding: utf-8 -*-
from importlib import import_module

import logging
import multiprocessing
import signal
from box import Box
from brewtils.models import Event
from multiprocessing.connection import Connection, Pipe
from multiprocessing.context import SpawnContext
from multiprocessing.queues import Queue
from types import FrameType
from typing import Any, Callable

import beer_garden
import beer_garden.config
import beer_garden.db.api as db
import beer_garden.events
import beer_garden.local_plugins.manager as lpm
import beer_garden.queue.api as queue
import beer_garden.router as router
from beer_garden.events.processors import PipeListener, QueueListener
from beer_garden.log import process_record

logger = logging.getLogger(__name__)


class EntryPoint:
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

    Class Attributes:

    Attributes:
        _signal_handler: Signal handler function that will be invoked (in the
            entry point process) when a SIGTERM is received
        _process: The actual entry point process object
        _ep_conn: End of communication pipe that is passed into the entry point
            process.
        _mp_conn: End of communication pipe that remains in the master process.
        _event_listener: Listens for events coming from the entry point.
    """

    def __init__(
        self,
        name: str,
        target: Callable,
        context: SpawnContext,
        log_queue: Queue,
        signal_handler: Callable[[int, FrameType], None],
        event_callback: Callable[[Event], None],
    ):
        self._name = name
        self._target = target
        self._context = context
        self._log_queue = log_queue
        self._signal_handler = signal_handler

        self._process = None
        self._ep_conn, self._mp_conn = Pipe()
        self._event_listener = PipeListener(
            conn=self._mp_conn,
            action=event_callback,
            name=f"{name} listener",
        )

    def start(self) -> None:
        """Start the entry point process"""
        process_name = f"BGEntryPoint-{self._name}"

        self._process = self._context.Process(
            name=process_name,
            target=self._target_wrapper,
            args=(
                beer_garden.config.get(),
                self._log_queue,
                self._target,
                self._signal_handler,
                self._ep_conn,
                lpm.lpm_proxy,
            ),
        )
        self._process.start()

        # And listen for events coming from it
        self._event_listener.start()

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
        # First stop listening for events
        self._event_listener.stop()

        # Then ensure the process is terminated
        self._process.terminate()
        self._process.join(timeout=timeout)

        if self._process.exitcode is None:
            logger.warning(
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
        self._mp_conn.send(event)

    @staticmethod
    def _target_wrapper(
        config: Box,
        log_queue: Queue,
        target: Callable,
        signal_handler: Callable[[int, FrameType], None],
        ep_conn: Connection,
        lpm_proxy,
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
            target:
            signal_handler:
            ep_conn:
            lpm_proxy:

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

        try:
            # Also set up plugin logging
            beer_garden.log.load_plugin_log_config()

            # Local plugin manager reference
            lpm.lpm_proxy = lpm_proxy

            # Set up a database connection
            db.create_connection(db_config=beer_garden.config.get("db"))

            # Set up message queue connections
            queue.create_clients(beer_garden.config.get("mq"))

            # Load known gardens for routing
            router.setup_routing()
        except Exception as ex:
            # If we don't do this any tracebacks won't propagate back to the "real"
            # logging. In systemd mode we don't see STDERR from entry points.
            logging.getLogger(__name__).exception(ex)

            raise Exception("Entry point initialization failed") from ex

        # Now invoke the actual process target, passing in the connection
        return target(ep_conn)


class Manager:
    """Entry points manager

    This is the way events are coordinated across entry points. This class does a
    couple of things:

    - Has a list of the entry points
    - Sets up a QueueProcessor for each of the entry point's upstream event queues. In
    other words, this class is listening for events coming from every entry point.
    - Allows registration of callbacks for certain types of events.
    - When an event is received from one of the entry point queues it will fire any
        callbacks registered for the event type.

    Attributes:
    """

    context: SpawnContext = None
    log_queue: Queue = None

    def __init__(self):
        self.entry_points = []
        self.context = multiprocessing.get_context("spawn")
        self.log_queue = self.context.Queue()

        self.log_reader = QueueListener(
            name="LogProcessor", queue=self.log_queue, action=process_record
        )

    def create_all(self):
        for entry_name, entry_value in beer_garden.config.get("entry").items():
            if entry_value.get("enabled"):
                try:
                    self.entry_points.append(self.create(entry_name))
                except Exception as ex:
                    logger.exception(f"Error creating entry point {entry_name}: {ex}")

    def create(self, module_name: str):
        module = import_module(f"beer_garden.api.{module_name}")

        return EntryPoint(
            name=module_name,
            target=module.run,
            context=self.context,
            log_queue=self.log_queue,
            signal_handler=module.signal_handler,
            event_callback=beer_garden.events.publish,
        )

    def start(self):
        self.log_reader.start()

        for entry_point in self.entry_points:
            entry_point.start()

    def stop(self):
        self.log_reader.stop()

        for entry_point in self.entry_points:
            entry_point.stop(timeout=10)

    def put(self, event: Event) -> None:
        """Publish an event to all entry points"""
        for entry_point in self.entry_points:
            entry_point.send_event(event)
