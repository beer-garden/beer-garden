# -*- coding: utf-8 -*-
from typing import Callable

from brewtils.models import Event
from brewtils.schema_parser import SchemaParser

from beer_garden.events.events_manager import EventProcessor


class PrintProcessor(EventProcessor):
    """Processor that just prints events to a stream"""

    def __init__(self, stream):
        super().__init__()
        self._stream = stream

    def process_next_message(self, event):
        print(SchemaParser.serialize(event), file=self._stream)


class RequeueProcessor(EventProcessor):
    """Processor that simply forwards events to another Queue"""

    def __init__(self, queue):
        super().__init__()
        self._queue = queue

    def process_next_message(self, event):
        self._queue.put(event)


class CallableProcessor(EventProcessor):
    """Processor that will invoke a given Callable with the event"""

    def __init__(self, callable_obj: Callable[[Event], None]):
        super().__init__()
        self._callable = callable_obj

    def process_next_message(self, event):
        self._callable(event)
