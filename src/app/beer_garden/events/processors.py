# -*- coding: utf-8 -*-
import logging
from multiprocessing import Queue
from queue import Empty
import beer_garden.config as config
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
    """

    def put(self, event: Event, skip_checked: bool = False):
        """Put a new item on the queue to be processed

        Args:
            event: New Event
        """
        
        # Check if event should be published to Rabbit
        if not skip_checked and (event.name in (
            Events.REQUEST_COMPLETED.name,
            Events.REQUEST_UPDATED.name,
            Events.REQUEST_CANCELED.name,
            Events.SYSTEM_CREATED.name,
            Events.SYSTEM_UPDATED.name,
            Events.SYSTEM_REMOVED.name,
            Events.GARDEN_UPDATED.name,
            Events.GARDEN_REMOVED.name,
        ) or (Events.GARDEN_SYNC.name and event.garden != config.get("garden.name"))):
            try:
                put_event(event)
            except:
                self.logger.error(f"Failed to publish Event: {event} to PIKA")
                self._queue.put(event)
        else:
            self._queue.put(event)
    
    def put_queue(self, event: Event):
        self._queue.put(event)