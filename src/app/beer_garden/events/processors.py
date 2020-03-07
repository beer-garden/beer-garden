# -*- coding: utf-8 -*-
import logging
from multiprocessing import Queue
from queue import Empty

from brewtils.models import Event, Events
from brewtils.stoppable_thread import StoppableThread

import beer_garden.events
import beer_garden.systems
import beer_garden.config


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
        """Process events as they are received """
        while not self.stopped():
            try:
                self.process(self._queue.get(timeout=0.1))
            except Empty:
                pass


class PipeListener(BaseProcessor):
    """Listens for items on a multiprocessing.connection.Connection"""

    def __init__(self, conn=None, **kwargs):
        super().__init__(**kwargs)
        self._conn = conn

    def run(self):
        """Process events as they are received """
        while not self.stopped():
            if self._conn.poll(0.1):
                self.process(self._conn.recv())


class FanoutProcessor(QueueListener):
    """Distributes items to multiple queues"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._processors = []
        self._processors_to_stop = []

    def run(self):
        super().run()

        for processor in self._processors_to_stop:
            if not processor.stopped():
                processor.stop()

    def process(self, event):
        for processor in self._processors:
            processor.put(event)

    def register(self, processor, start: bool = True):
        """Register and start a downstream Processor

        Args:
            processor: The Processor to register
            start: Whether to start the processor being added
        """
        self._processors.append(processor)

        if start:
            self._processors_to_stop.append(processor)
            processor.start()


class HttpEventProcessor(QueueListener):
    """Publish events using an EasyClient"""

    def __init__(self, easy_client=None, black_list=None, **kwargs):
        super().__init__(**kwargs)

        self._ez_client = easy_client
        self._black_list = black_list or []

    def process(self, event: Event):
        try:
            if event.name not in self._black_list:
                event.garden = beer_garden.config.get("garden.name")
                self._ez_client.publish_event(event)
        except Exception as ex:
            logger.exception(f"Error publishing EasyClient event: {ex}")
