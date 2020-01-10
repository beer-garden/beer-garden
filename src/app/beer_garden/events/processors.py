# -*- coding: utf-8 -*-
from brewtils.schema_parser import SchemaParser

from beer_garden.events.events_manager import EventProcessor


class PrintProcessor(EventProcessor):
    """Processor that just prints events to a stream"""

    def __init__(self, stream):
        super().__init__()
        self._stream = stream

    def process_next_message(self, event):
        print(SchemaParser.serialize(event), file=self._stream)
