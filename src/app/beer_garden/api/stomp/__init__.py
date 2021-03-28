# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
import logging
import threading
import types
from brewtils.models import Event, Events

import beer_garden.config as config
import beer_garden.events
from beer_garden.api.stomp.manager import StompManager, EventManager
from beer_garden.events import publish
from beer_garden.garden import get_gardens

logger: logging.Logger = logging.getLogger(__name__)
shutdown_event = threading.Event()


def run(ep_conn):
    conn_manager = StompManager()

    _setup_event_handling(StompManager, ep_conn)

    entry_config = config.get("entry.stomp")
    parent_config = config.get("parent.stomp")
    garden_name = config.get("garden.name")

    if entry_config.get("enabled"):
        conn_manager.add_connection(
            stomp_config=entry_config, name=f"{garden_name}_entry", is_main=True
        )

    if parent_config.get("enabled"):
        conn_manager.add_connection(
            stomp_config=parent_config, name=f"{garden_name}_parent", is_main=True
        )

    for garden in get_gardens(include_local=False):
        if garden.name != garden_name and garden.connection_type:
            if garden.connection_type.casefold() == "stomp":
                connection_params = StompManager.format_connection_params(
                    "stomp_", garden.connection_params
                )
                connection_params["send_destination"] = None
                conn_manager.add_connection(
                    stomp_config=connection_params, name=garden.name
                )

    conn_manager.start()

    logger.info("Stomp entry point started")

    publish(
        Event(name=Events.ENTRY_STARTED.name, metadata={"entry_point_type": "STOMP"})
    )

    while not shutdown_event.wait(10):
        for name, info in conn_manager.conn_dict.items():
            connection = info.get("conn")

            if connection:
                logger.debug(f"{name}: Checking connection")
                if not connection.is_connected() and connection.bg_active:
                    logger.debug(f"{name}: Attempting to reconnect")

                    if connection.connect():
                        logger.debug(f"{name}: Reconnect successful")
                    else:
                        logger.debug(f"{name}: Reconnect failed")

    conn_manager.shutdown()
    conn_manager.stop()
    conn_manager.join(5)

    beer_garden.events.manager.stop()


def _setup_event_handling(stomp_manager, ep_conn):
    beer_garden.events.manager = EventManager(
        action=stomp_manager.handle_event, conn=ep_conn
    )


def signal_handler(_: int, __: types.FrameType):
    shutdown_event.set()
