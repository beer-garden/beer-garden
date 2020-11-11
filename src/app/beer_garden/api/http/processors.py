# -*- coding: utf-8 -*-
import logging

from brewtils.schema_parser import SchemaParser

import beer_garden.api.http
from beer_garden.api.http.handlers.v1.event import EventSocket

logger = logging.getLogger(__name__)


class EventManager:
    """Will simply push events across the connection to the master process"""

    def __init__(self, conn):
        self._conn = conn

    def put(self, event):
        beer_garden.api.http.io_loop.add_callback(self._conn.send, event)


def websocket_publish(item):
    """Will serialize an event and publish it to all event websocket endpoints"""
    try:
        beer_garden.api.http.io_loop.add_callback(
            EventSocket.publish, SchemaParser.serialize(item, to_string=True)
        )
    except Exception as ex:
        logger.exception(f"Error publishing event to websocket: {ex}")
