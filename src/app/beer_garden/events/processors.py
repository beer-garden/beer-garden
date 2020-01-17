# -*- coding: utf-8 -*-
from functools import partial
from multiprocessing import Queue
from pprint import pprint
from queue import Empty
from typing import Callable, Union

from brewtils.schema_parser import SchemaParser
from brewtils.stoppable_thread import StoppableThread


class QueueProcessor(StoppableThread):
    """Base Processor"""

    def __init__(self, queue=None, **kwargs):
        super().__init__(**kwargs)

        self._queue = queue or Queue()

    def put(self, item):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """
        self._queue.put(item)

    def process(self, item):
        """Process an item"""
        pass

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


class FanoutProcessor(QueueProcessor):
    """Distributes items to multiple processors"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._processors = []

    def run(self):
        super().run()

        for processor in self._processors:
            if not processor.stopped():
                processor.stop()

    def process(self, event):
        for processor in self._processors:
            processor.put(event)

    def register(self, processor: QueueProcessor, start: bool = True):
        """Register and start a downstream Processor

        Args:
            processor: The Processor to register
            start: Whether to start the processor being added
        """
        self._processors.append(processor)

        if start:
            processor.start()


class PrettyPrinter(QueueProcessor):
    """Processor that just prints serialized models to a stream"""

    def __init__(self, stream, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream

    def process(self, item):
        pprint(SchemaParser.serialize(item, to_string=False), stream=self._stream)


class RequeueProcessor(QueueProcessor):
    """Processor that simply forwards items to another Queue"""

    def __init__(self, target_queue, **kwargs):
        super().__init__(**kwargs)
        self._target_queue = target_queue

    def process(self, item):
        self._target_queue.put(item)


class CallableProcessor(QueueProcessor):
    """Processor that will invoke a given callable or partial with the item"""

    def __init__(
        self, callable_obj: Union[Callable[[object], None], partial], **kwargs
    ):
        super().__init__(**kwargs)
        self._callable = callable_obj

    def process(self, item):
        self._callable(item)
