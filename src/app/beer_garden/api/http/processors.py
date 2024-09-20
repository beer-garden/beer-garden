# -*- coding: utf-8 -*-
import logging

import beer_garden.api.http
import beer_garden.config as config
from beer_garden.api.http.handlers.v1.event import EventSocket

logger = logging.getLogger(__name__)


class EventManager:
    """Will simply push events across the connection to the master process"""

    def __init__(self, conn):
        self._conn = conn

    def put(self, event):
        beer_garden.api.http.io_loop.add_callback(self._conn.send, event)


def websocket_publish(event):
    """Publish an event to all websocket endpoints"""
    if event.garden != config.get("garden.name") or event.error:
        return

    try:
        beer_garden.api.http.io_loop.add_callback(EventSocket.publish, event)
    except Exception as ex:
        logger.exception(f"Error publishing event to websocket: {ex}")
