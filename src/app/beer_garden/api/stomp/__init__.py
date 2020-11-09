# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
import logging
import types

import beer_garden.config as config
from brewtils.models import Event, Events
from beer_garden.api.stomp.stomp_manager import StompManager
from beer_garden.events import publish

logger = logging.getLogger(__name__)
st_manager_stack = []


def run(ep_conn):
    global st_manager_stack
    stomp_config = config.get("entry.stomp")
    host_and_ports = [(stomp_config.host, stomp_config.port)]
    logger.debug(
        "Starting Stomp entry point on host and port: " + host_and_ports.__str__()
    )
    st_manager = StompManager(ep_conn=ep_conn, stomp_config=stomp_config)

    st_manager.start()
    st_manager_stack.append(st_manager)
    logger.info("Stomp entry point started")

    publish(Event(name=Events.ENTRY_STARTED.name))


def signal_handler(_: int, __: types.FrameType):
    global st_manager_stack
    while st_manager_stack:
        st_manager_stack.pop().stop()
