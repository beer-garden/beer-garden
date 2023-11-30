# -*- coding: utf-8 -*-
import logging
from multiprocessing import Queue
from queue import Empty
from brewtils.models import Event, Events
from brewtils.stoppable_thread import StoppableThread
from brewtils.schema_parser import SchemaParser
from beer_garden.queue.rabbit import put_event
from pika.spec import PERSISTENT_DELIVERY_MODE
import threading

from concurrent.futures.thread import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class BaseProcessor(StoppableThread):
    """Base Processor"""

    def __init__(self, action=None, **kwargs):
        super().__init__(**kwargs)

        self._action = action

    def process(self, item):
        try:
            self._action(item)
        except Exception as ex:
            logger.exception(f"Error processing: {ex}")

    def put(self, item):
        self.process(item)


class QueueListener(BaseProcessor):
    """Listens for items on a multiprocessing.Queue"""

    def __init__(self, queue=None, **kwargs):
        super().__init__(**kwargs)

        self._queue = queue or Queue()

    def put(self, item):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """
        self._queue.put(item)

    def clear(self):
        """Empty the underlying queue without processing items"""
        while not self._queue.empty():
            self._queue.get()

    def run(self):
        """Process events as they are received"""
        while not self.stopped():
            try:
                self.process(self._queue.get(timeout=0.1))
            except Empty:
                pass


class DelayListener(QueueListener):
    """Listener that waits for an Event before running"""

    def __init__(self, event=None, **kwargs):
        super().__init__(**kwargs)

        self._event = event

    def run(self):
        self._event.wait()

        super().run()


class PipeListener(BaseProcessor):
    """Listens for items on a multiprocessing.connection.Connection"""

    def __init__(self, conn=None, **kwargs):
        super().__init__(**kwargs)
        self._conn = conn

    def run(self):
        """Process events as they are received"""
        while not self.stopped():
            if self._conn.poll(0.1):
                self.process(self._conn.recv())


class FanoutProcessor(QueueListener):
    """Distributes items to multiple queues"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._processors = []
        self._managed_processors = []

    def run(self):
        for processor in self._managed_processors:
            processor.start()

        super().run()

        for processor in self._managed_processors:
            if not processor.stopped():
                processor.stop()

    def process(self, event):
        for processor in self._processors:
            processor.put(event)

    def register(self, processor, manage: bool = True):
        """Register and start a downstream Processor

        Args:
            processor: The Processor to register
            manage: Whether to start and stop the processor being added
        """
        self._processors.append(processor)

        if manage:
            self._managed_processors.append(processor)


class EventProcessor(FanoutProcessor):
    """Class responsible for coordinating Event processing

    The EventProcessor is responsible for the following:
    - Defining on_message_received callback that will be invoked by the PikaConsumer
    - Parsing the event
    - Placing event in queue

    Args:
        target: Incoming requests will be invoked on this object
        logger: A logger
        max_workers: Max number of threads to use in the executor pool
    """

    def __init__(
        self,
        logger=None,
        max_workers=None,
        **kwargs
    ):
        super().__init__(**kwargs)

    def stop(self):
        self.shutdown_event.set()
        self.shutdown()
        super().stop()
        
    def run(self):
        self.startup()

    def setup(self, **kwargs):
        self.logger = logger or logging.getLogger(__name__)

        from brewtils.pika import PikaConsumer
        self.shutdown_event = threading.Event()

        self.consumer =  PikaConsumer(panic_event = self.shutdown_event, **kwargs)

        self.consumer.on_message_callback = self.on_message_received

        self._pool = ThreadPoolExecutor(max_workers=kwargs.get("max_workers", 1))

    def put(self, event: Event):
        """Put a new item on the queue to be processed

        Args:
            event: New Event
        """
        
        # Check if it should be published to Rabbit
        if event.name in (
            Events.REQUEST_COMPLETED.name,
            Events.REQUEST_UPDATED.name,
            Events.REQUEST_CANCELED.name,
            Events.SYSTEM_CREATED.name,
            Events.SYSTEM_UPDATED.name,
            Events.SYSTEM_REMOVED.name,
            Events.GARDEN_UPDATED.name,
            Events.GARDEN_REMOVED.name,
        ) or (Events.GARDEN_SYNC.name and event.garden != config.get("garden.name")):
            put_event(event, 
                      confirm=True,
                      mandatory=True,
                      delivery_mode=PERSISTENT_DELIVERY_MODE)
        else:
            self._queue.put(event)


    def on_message_received(self, message, headers):
        """Callback function that will be invoked for received messages

        This will attempt to parse the message and then run the parsed Request through
        all validation functions that this RequestProcessor knows about.

        If the request parses cleanly and passes validation it will be submitted to this
        RequestProcessor's ThreadPoolExecutor for processing.

        Args:
            message: The message string
            headers: The header dictionary

        Returns:
            A future that will complete when processing finishes

        Raises:
            DiscardMessageException: The request failed to parse correctly
            RequestProcessException: Validation failures should raise a subclass of this
        """
        event = self._parse(message)

        return self._pool.submit(
            self.process_message, event
        )

    def process_message(self, event: Event):
        """Process a message. Intended to be run on an Executor.

        Will set the status to IN_PROGRESS, invoke the command, and set the final
        status / output / error_class.

        Args:
            target: The object to invoke received commands on
            request: The parsed Request
            headers: Dictionary of headers from the `PikaConsumer`

        Returns:
            None
        """
      
        self._queue.put(event)


    def startup(self):
        """Start the RequestProcessor"""
        self.consumer.start()
        self.consumer.run()

    def shutdown(self):
        """Stop the RequestProcessor"""
        self.logger.debug("Shutting down consumer")
        self.consumer.stop_consuming()

        # Finish all current actions
        self._pool.shutdown(wait=True)

        self.consumer.stop()
        self.consumer.join()

        # Give the updater a chance to shutdown
        self._updater.shutdown()

    def _parse(self, message):
        """Parse a message using the standard SchemaParser

        Args:
            message: The raw (json) message body

        Returns:
            A Request model

        Raises:
            DiscardMessageException: The request failed to parse correctly
        """
        try:
            return SchemaParser.parse_event(message, from_string=True)
        except Exception as ex:
            self.logger.exception(
                "Unable to parse message body: {0}. Exception: {1}".format(message, ex)
            )
            raise DiscardMessageException("Error parsing message body")