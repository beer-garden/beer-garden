# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
import logging
import time
import types

import beer_garden.config as config
from tornado.ioloop import IOLoop
from brewtils.models import Event, Events, Request, Operation
import beer_garden.events
import beer_garden.router

from beer_garden.api.stomp.processors import EventManager
from beer_garden.api.stomp.server import Connection
from beer_garden.events import publish
from beer_garden.events.processors import QueueListener

logger = None
conn = None

io_loop = None


def run(ep_conn):
    global logger, conn, io_loop
    logger = logging.getLogger(__name__)
    stomp_config = config.get("entry.stomp")
    logger.info("Starting Stomp entry point on host and port: "+[(stomp_config.host, stomp_config.port)].__str__())
    conn = Connection()
    conn.connect("connected")
    io_loop = IOLoop.current()
    _setup_operation_forwarding()

    logger.debug("Starting forward processor")
    beer_garden.router.forward_processor.start()

    _setup_event_handling(ep_conn)
    logger.info("Stomp entry point started")
    io_loop.start()
    publish(Event(name=Events.ENTRY_STARTED.name))


def signal_handler(_: int, __: types.FrameType):
    io_loop.add_callback_from_signal(shutdown)


def shutdown():
    global conn, logger, io_loop
    conn.disconnect()
    logger.debug("Stopping forward processing")
    beer_garden.router.forward_processor.stop()
    # This will almost definitely not be published because it would need to make it up
    # to the main process and back down into this process. We just publish this here in
    # case the main process is looking for it.

    logger.debug("Stopping IO loop")
    publish(Event(name=Events.ENTRY_STOPPED.name))
    io_loop.add_callback(io_loop.stop)


def _setup_operation_forwarding():
    beer_garden.router.forward_processor = QueueListener(
        action=beer_garden.router.forward
    )


def _setup_event_handling(ep_conn):
    # This will push all events generated in the entry point up to the master process
    global io_loop
    beer_garden.events.manager = EventManager(ep_conn)
    io_loop.add_handler(ep_conn, lambda c, _: _event_callback(c.recv()), IOLoop.READ)


def reconnect():
    global conn, logger
    if not conn.is_connected():
        logger.warning("Lost stomp connection")
        conn.connect("reconnected")


def _event_callback(event):
    # Register handlers that the entry point needs to care about
    # As of now that's only the routing subsystem
    for event_handler in [beer_garden.router.handle_event, handle_event]:
        try:
            event_handler(event)
        except Exception as ex:
            logger.exception(f"Error executing callback for {event!r}: {ex}")


def handle_event(event):
    global conn
    reconnect()
    conn.send_event(event)
