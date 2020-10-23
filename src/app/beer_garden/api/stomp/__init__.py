# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
import logging
import types

import beer_garden.config as config
from brewtils.models import Event, Events
import beer_garden.events
import beer_garden.router
import threading
from beer_garden.api.stomp.processors import EventManager
from beer_garden.api.stomp.server import Connection
from beer_garden.events import publish
from beer_garden.events.processors import QueueListener

logger = logging.getLogger(__name__)
conn = None
th = None
stop_thread = False


def run(ep_conn):
    global conn
    stomp_config = config.get("entry.stomp")
    logger.info(
        "Starting Stomp entry point on host and port: "
        + [(stomp_config.host, stomp_config.port)].__str__()
    )
    conn = Connection()
    conn.connect("connected")
    _setup_operation_forwarding()

    logger.debug("Starting forward processor")
    beer_garden.router.forward_processor.start()

    _setup_event_handling(ep_conn)
    logger.info("Stomp entry point started")
    th.start()
    publish(Event(name=Events.ENTRY_STARTED.name))


def signal_handler(_: int, __: types.FrameType):
    shutdown()


def shutdown():
    global stop_thread
    conn.disconnect()
    logger.debug("Stopping forward processing")
    beer_garden.router.forward_processor.stop()
    # This will almost definitely not be published because it would need to make it up
    # to the main process and back down into this process. We just publish this here in
    # case the main process is looking for it.

    logger.debug("Stopping IO loop")
    publish(Event(name=Events.ENTRY_STOPPED.name))
    stop_thread = True


def _setup_operation_forwarding():
    beer_garden.router.forward_processor = QueueListener(
        action=beer_garden.router.forward
    )


def _setup_event_handling(ep_conn):
    # This will push all events generated in the entry point up to the master process
    global th
    beer_garden.events.manager = EventManager(ep_conn)
    th = threading.Thread(_event_thread(ep_conn))


def _event_thread(ep_conn):
    while True:
        if ep_conn.poll():
            handle_event(ep_conn.recv())
        if stop_thread:
            break


def reconnect():
    if not conn.is_connected():
        logger.warning("Lost stomp connection")
        conn.connect("reconnected")


def handle_event(event):
    reconnect()
    conn.send_event(event)
