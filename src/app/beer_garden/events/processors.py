# -*- coding: utf-8 -*-
import logging
import traceback
import uuid
from copy import deepcopy
from multiprocessing import Queue
from queue import Empty

import elasticapm
from brewtils.models import Event, Events
from brewtils.stoppable_thread import StoppableThread

import beer_garden.config as config
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


class InternalQueueListener(QueueListener):
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

    def handle_event(self, event):
        try:
            if config.get("apm.enabled") and elasticapm.get_client():
                with elasticapm.capture_span(name=event.name, span_type="Event"):
                    if hasattr(event, "payload") and hasattr(event.payload, "id"):
                        elasticapm.set_custom_context({"id": event.payload.id})
                    self._handler(deepcopy(event))

            else:
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
            self._queue.put(event)


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
                self._queue.put(event)
            except Exception:
                self.logger.error(f"Failed to publish Event: {event} to PIKA")
                self._queue.put(event)
        elif (
            "_source_uuid" not in event.metadata
            or event.metadata["_source_uuid"] != self.uuid
        ):
            self._queue.put(event)

    def put_queue(self, event: Event):
        self._queue.put(event)
