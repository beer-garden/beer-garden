# -*- coding: utf-8 -*-
import logging

from brewtils.schema_parser import SchemaParser

import beer_garden.api.http
import beer_garden.api.http.handlers.v1 as v1

logger = logging.getLogger(__name__)


class EventManager:
    """Will simply push events across the connection to the master process"""

    def __init__(self, conn):
        self._conn = conn

    def put(self, event):
        self._conn.send(event)


def websocket_publish(item):
    """Will serialize an event and publish it to all event websocket endpoints"""
    try:
        # So we're going to need a better way to do this
        if item.payload:
            item.payload = SchemaParser.serialize(item.payload)
        if item.metadata:
            item.metadata = {}

        serialized = SchemaParser.serialize(item, to_string=True)

        beer_garden.api.http.io_loop.add_callback(
            v1.event.EventSocket.publish, serialized
        )
    except Exception as ex:
        logger.exception(f"{ex}")
