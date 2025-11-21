# -*- coding: utf-8 -*-
import datetime
import logging
import os
import sys
import time
import uuid
from collections import deque
from copy import deepcopy
from multiprocessing import Queue
from queue import Empty

import elasticapm
from brewtils.models import Event, Events, Request
from brewtils.schema_parser import SchemaParser
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
        self._schema_parser = SchemaParser()

    def process(self, item):
        try:
            self._action(item)
            del item
        except Exception as ex:
            logger.exception(f"Error processing: {ex}")

    def put(self, item):
        self.process(item)

    def clone(self, item):

        if (
            isinstance(item, Event)
            and hasattr(item, "payload")
            and item.payload_type == "Request"
        ):
            # If payload is a Request, we need to check if the output is large
            # and if so, we will serialize it to avoid memory issues
            if (
                hasattr(item.payload, "output")
                and item.payload.output is not None
                and sys.getsizeof(item.payload.output) > 1000000
            ):
                return self._schema_parser.parse_event(
                    self._schema_parser.serialize_event(item, to_string=False),
                    from_string=False,
                )

        return deepcopy(item)


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

        self._data = {}
        self._unique_data = unique_data

    def put(self, event: Event):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """

        try:
            if (
                self._unique_data
                and hasattr(event, "payload")
                and event.payload is not None
                and hasattr(event.payload, "id")
                and event.payload.id is not None
                and hasattr(event.payload, "is_newer")
            ):

                if str(event.payload.id) in self._data:
                    ref = self._data[event.payload.id]
                    if isinstance(event.payload, type(ref.payload)):
                        if event.payload.is_newer(ref.payload):
                            # Collect Request Metadata
                            # If this expands past Requests, we'll need to refactor
                            if isinstance(event.payload, Request):
                                for metadata_key in ref.payload.metadata:
                                    if metadata_key not in event.payload.metadata:
                                        event.payload.metadata[metadata_key] = (
                                            ref.payload.metadata[metadata_key]
                                        )
                                if ref.payload.status is not event.payload.status:
                                    status_key = (
                                        f"{ref.payload.status}_"
                                        f"{config.get('garden.name')}"
                                    )
                                    if status_key not in event.payload.metadata:
                                        event.payload.metadata[status_key] = int(
                                            datetime.datetime.now(
                                                datetime.timezone.utc
                                            ).timestamp()
                                            * 1000
                                        )

                            self._data[str(event.payload.id)] = event

                            del ref
                        else:
                            del event
                    else:
                        # Type Mis-match, just process the event
                        super().put(event)

                    return

                self._data[str(event.payload.id)] = event
                self._queue.append(str(event.payload.id))

            else:
                super().put(event)
        except Exception as ex:
            # All exceptions must be captured. If raised, then the queue processor could stop
            # processing events.
            logger.error(
                "Error while putting event on %s: %s. Error: %s",
                self.name,
                event,
                ex,
            )

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
                        ref = self._data.pop(ref, None)
                    if ref:
                        self.process(ref)
                except IndexError:
                    if self._unique_data and self._data:
                        ref = self._data.pop(next(iter(self._data)))
                        if ref:
                            self.process(ref)
                    else:
                        time.sleep(0.1)
                except Exception as ex:
                    logger.error(
                        "Error while processing event from %s: %s. Error: %s",
                        self.name,
                        ref,
                        ex,
                    )

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

    def __init__(
        self,
        handler,
        local_only=False,
        filters=None,
        filter_func=None,
        allow_api_only=False,
        **kwargs,
    ):
        super().__init__(action=self.handle_event, **kwargs)

        self._filters = []

        if filters:
            for filter in filters:
                self._filters.append(filter.name)

        self._filter_func = filter_func

        self._handler = handler
        self._handler_tag = self._name
        self._local_only = local_only

        self._transaction_type = self._name
        self.allow_api_only = allow_api_only

    def handle_event(self, event):
        trace_parent_header = None
        if config.get("metrics.elastic.enabled"):
            if hasattr(event, "metadata") and "_trace_parent" in event.metadata:
                trace_parent_header = event.metadata["_trace_parent"]
            elif elasticapm.get_trace_parent_header() is not None:
                trace_parent_header = elasticapm.get_trace_parent_header()

        try:
            with CollectMetrics(
                "Queue_Event",
                f"QUEUE_POP::{self._handler_tag}",
                trace_parent_header=trace_parent_header,
            ):
                if config.get("metrics.elastic.enabled"):
                    extract_custom_context(event)

                self._handler(event)
        except Exception as ex:
            _, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(
                "'%s' handler received an error executing callback for event %s: %s: %s Line %s"
                % (
                    self._handler_tag,
                    repr(event),
                    str(ex),
                    fname,
                    exc_tb.tb_lineno,
                )
            )

    def filter_event(self, event):

        if not self._filters or event.name not in self._filters:
            return True

        if event.error:
            return True

        if self._local_only and event.garden != config.get("garden.name"):
            return True

        if event.metadata.get("API_ONLY", False) and not self.allow_api_only:
            return True

        if self._filter_func and self._filter_func(event):
            return True

        return False

    def put(self, event: Event):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """

        if not self.filter_event(event):
            trace_parent_header = None
            if config.get("metrics.elastic.enabled"):
                if hasattr(event, "metadata") and "_trace_parent" in event.metadata:
                    trace_parent_header = event.metadata["_trace_parent"]
                elif elasticapm.get_trace_parent_header() is not None:
                    trace_parent_header = elasticapm.get_trace_parent_header()

                if hasattr(event, "metadata") and "_trace_parent" not in event.metadata:
                    event.metadata["_trace_parent"] = trace_parent_header

            with CollectMetrics(
                "Queue_Event",
                f"QUEUE_PUT::{self._name}",
                trace_parent_header=trace_parent_header,
            ):
                if config.get("metrics.elastic.enabled"):
                    extract_custom_context(event)
                super().put(self.clone(event))


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
