# -*- coding: utf-8 -*-
from multiprocessing import Queue
from queue import Empty

from brewtils.stoppable_thread import StoppableThread


class BaseProcessor(StoppableThread):
    """Base Processor"""

    def __init__(self, action=None, **kwargs):
        super().__init__(**kwargs)

        self._action = action

    def process(self, item):
        self._action(item)


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


# class FanoutProcessor(QueueProcessor):
#     """Distributes items to multiple queues"""
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#         self._processors = []
#
#     def run(self):
#         super().run()
#
#         for processor in self._processors:
#             if not processor.stopped():
#                 processor.stop()
#
#     def process(self, event):
#         for processor in self._processors:
#             processor.put(event)
#
#     def register(self, processor: QueueProcessor, start: bool = True):
#         """Register and start a downstream Processor
#
#         Args:
#             processor: The Processor to register
#             start: Whether to start the processor being added
#         """
#         self._processors.append(processor)
#
#         if start:
#             processor.start()
