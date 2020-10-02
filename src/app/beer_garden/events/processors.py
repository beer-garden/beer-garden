# -*- coding: utf-8 -*-
import logging
from multiprocessing import Queue
from queue import Empty

from brewtils.stoppable_thread import StoppableThread

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
        """Process events as they are received """
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
