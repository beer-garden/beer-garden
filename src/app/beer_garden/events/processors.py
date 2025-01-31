# -*- coding: utf-8 -*-
import logging
import threading
import time
import traceback
import uuid
from collections import deque
from copy import deepcopy
from multiprocessing import Queue
from queue import Empty

from brewtils.models import Event, Events
from brewtils.stoppable_thread import StoppableThread

import beer_garden.config as config
from beer_garden.metrics import CollectMetrics, extract_custom_context
from beer_garden.queue.rabbit import put_event

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


class DequeListener(BaseProcessor):
    """Listens for items on a collections.deque"""

    def __init__(self, queue=None, **kwargs):
        super().__init__(**kwargs)

        self._queue = queue or deque()

    def put(self, item):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """
        self._queue.append(item)

    def clear(self):
        """Empty the underlying queue without processing items"""
        self._queue.clear()

    def run(self):
        """Process events as they are received"""
        while not self.stopped():
            try:
                self.process(self._queue.popleft())
            except IndexError:
                time.sleep(0.1)

    def queue_depth(self):
        return len(self._queue)


class DequeSetListener(DequeListener):
    """Listens for items on a multiprocessing.Queue"""

    def __init__(self, queue=None, unique_data=False, **kwargs):
        super().__init__(**kwargs)

        self._lock = threading.RLock()
        self._data = {}
        self._unique_data = unique_data

    def put(self, event: Event):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """

        if (
            self._unique_data
            and hasattr(event, "payload")
            and hasattr(event.payload, "id")
            and hasattr(event.payload, "is_newer")
        ):
            with self._lock:
                if event.payload.id in self._data:
                    ref = self._data[event.payload.id]
                    if isinstance(event.payload, type(ref.payload)):
                        if event.payload.is_newer(ref.payload):
                            self._data[str(event.payload.id)] = deepcopy(event)
                    else:
                        # Type Mis-match, just process the event
                        super().put(event)
                        return
                else:
                    self._data[str(event.payload.id)] = deepcopy(event)
                    self._queue.append(str(event.payload.id))

        else:
            super().put(event)

    def clear(self):
        """Empty the underlying queue without processing items"""

        super().clear()
        if self._unique_data:
            self._data = {}

    def run(self):
        """Process events as they are received"""
        if not self._unique_data:
            super().run()
        else:
            while not self.stopped():
                try:
                    ref = self._queue.popleft()
                    if isinstance(ref, str):
                        with self._lock:
                            ref = self._data.pop(ref, None)
                    if ref:
                        self.process(ref)
                except IndexError:
                    if self._unique_data and self._data:
                        ref = None
                        with self._lock:
                            ref = self._data.pop(next(iter(self._data)))
                        if ref:
                            self.process(ref)
                    else:
                        time.sleep(0.1)

    def queue_depth(self):
        if not self._unique_data:
            return super().queue_depth()
        return len(self._data)


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

    def queue_depth(self):
        return self._queue.qsize()


class InternalQueueListener(DequeSetListener):
    """Listener for internal events only"""

    def __init__(self, handler, handler_tag, local_only=False, filters=None, **kwargs):
        super().__init__(action=self.handle_event, **kwargs)

        self._filters = []

        if filters:
            for filter in filters:
                self._filters.append(filter.name)

        self._handler = handler
        self._handler_tag = handler_tag
        self._local_only = local_only

        self._transaction_type = handler_tag

    def handle_event(self, event):
        trace_parent_header = None
        if (
            config.get("metrics.elastic.enabled")
            and hasattr(event, "metadata")
            and "_trace_parent" in event.metadata
        ):
            trace_parent_header = event.metadata["_trace_parent"]

        with CollectMetrics(
            "Queue_Event",
            f"QUEUE_POP::{self._handler_tag}",
            trace_parent_header=trace_parent_header,
        ):
            try:
                if config.get("metrics.elastic.enabled"):
                    extract_custom_context(event)

                self._handler(deepcopy(event))
            except Exception as ex:
                logger.error(
                    "'%s' handler received an error executing callback for event %s: %s: %s"
                    % (
                        self._handler_tag,
                        repr(event),
                        str(ex),
                        traceback.TracebackException.from_exception(ex),
                    )
                )

    def put(self, event: Event):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """

        if not self._filters:
            return

        if event.error:
            return

        if self._local_only and event.garden != config.get("garden.name"):
            return

        if event.metadata.get("API_ONLY", False):
            return

        if event.name in self._filters:
            trace_parent_header = None
            if (
                config.get("metrics.elastic.enabled")
                and hasattr(event, "metadata")
                and "_trace_parent" in event.metadata
            ):
                trace_parent_header = event.metadata["_trace_parent"]

            with CollectMetrics(
                "Queue_Event",
                f"QUEUE_PUT::{self._handler_tag}",
                trace_parent_header=trace_parent_header,
            ):
                super().put(event)


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


class FanoutProcessor(DequeListener):
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


class ReplicationProcessor(FanoutProcessor):
    """Class responsible for coordinating Event processing"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.uuid = str(uuid.uuid4())

    def put(self, event: Event, skip_checked: bool = False):
        """Put a new item on the queue to be processed

        Args:
            event: New Event
            skip_check: Flag to skip Event Name checks for routing
        """

        # Check if event should be published to Rabbit
        if (
            not skip_checked
            and event.name != Events.REQUEST_TOPIC_PUBLISH.name
            and (
                event.name != Events.GARDEN_SYNC.name
                or (
                    event.name == Events.GARDEN_SYNC.name
                    and event.garden != config.get("garden.name")
                )
            )
        ):
            try:
                event.metadata["_source_uuid"] = self.uuid
                put_event(event)
                super().put(event)
            except Exception:
                self.logger.error(f"Failed to publish Event: {event} to PIKA")
                super().put(event)
        elif (
            "_source_uuid" not in event.metadata
            or event.metadata["_source_uuid"] != self.uuid
        ):
            super().put(event)

    def put_queue(self, event: Event):
        super().put(event)
