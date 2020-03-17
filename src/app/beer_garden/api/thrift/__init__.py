# -*- coding: utf-8 -*-
"""Package containing the Thrift entry point

This is DEPRECATED and will not be released in a stable version. It's included here
purely as a testing tool.

Note that thriftpy2 is not listed in the project's dependencies. If you want to run this
entry point you must install thriftpy2 first.
"""

import logging
import os
import types

import thriftpy2
from brewtils.models import Event, Events

import beer_garden.events
import beer_garden.router
from beer_garden.api.http import EventManager
from beer_garden.api.thrift.handler import BartenderHandler
from beer_garden.api.thrift.server import make_server
from beer_garden.events import publish
from beer_garden.events.processors import QueueListener

logger = None
the_server = None

bg_thrift = thriftpy2.load(
    os.path.join(os.path.dirname(__file__), "beergarden.thrift"),
    module_name="bg_thrift",
)


def run(ep_conn):
    global logger, the_server
    logger = logging.getLogger(__name__)

    # TODO: The thrift portion is currently hardcoded, because it should
    # no longer be in the config. Eventually the thrift thread will be removed.
    the_server = make_server(
        service=bg_thrift.BartenderBackend,
        handler=BartenderHandler(),
        host="0.0.0.0",
        port=9090,
    )

    _setup_operation_forwarding()
    _setup_event_handling(ep_conn)

    logger.debug("Starting forward processor")
    beer_garden.router.forward_processor.start()

    publish(Event(name=Events.ENTRY_STARTED.name))

    logger.info("Starting Thrift server")
    the_server.run()
    logger.info("Thrift server is shut down. Goodbye!")


def signal_handler(_: int, __: types.FrameType):
    logger.debug("Stopping forward processing")
    beer_garden.router.forward_processor.stop()

    # This will almost definitely not be published because it would need to make it up
    # to the main process and back down into this process. We just publish this here in
    # case the main process is looking for it.
    publish(Event(name=Events.ENTRY_STOPPED.name))

    the_server.stop()


def _setup_operation_forwarding():
    # Create a forwarder to push operations to child gardens
    # TODO - This thing is another thread. Asyncing it would be nice
    beer_garden.router.forward_processor = QueueListener(
        action=beer_garden.router.forward
    )


def _setup_event_handling(ep_conn):
    # This will push all events generated in the entry point up to the master process
    beer_garden.events.manager = EventManager(ep_conn)

    # TODO - For this to work we'd need to process events coming from the main process
    # io_loop.add_handler(ep_conn, lambda c, _: _event_callback(c.recv()), IOLoop.READ)


def _event_callback(event):
    # Register handlers that the entry point needs to care about
    # As of now that's only the routing subsystem
    for event_handler in [beer_garden.router.handle_event]:
        try:
            event_handler(event)
        except Exception as ex:
            logger.exception(f"Error executing callback for {event!r}: {ex}")
