# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
import logging
import types

import beer_garden.config as config
from brewtils.models import Event, Events
from beer_garden.api.stomp.stomp_manager import StompManager, shutdown
from beer_garden.events import publish

logger = logging.getLogger(__name__)


def run(ep_conn):
    stomp_config = config.get("entry.stomp")
    host_and_ports = [(stomp_config.host, stomp_config.port)]
    logger.info(
        "Starting Stomp entry point on host and port: " + host_and_ports.__str__()
    )
    st_manager = StompManager(ep_conn=ep_conn, stomp_config=stomp_config)
    logger.info("Stomp entry point started")
    st_manager.start_thread()
    publish(Event(name=Events.ENTRY_STARTED.name))


def signal_handler(_: int, __: types.FrameType):
    shutdown()
