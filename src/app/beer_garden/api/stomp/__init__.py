# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
from typing import Optional

import logging
import types

import beer_garden.config as config
from brewtils.models import Event, Events
from beer_garden.api.stomp.manager import StompManager
from beer_garden.events import publish
from beer_garden.garden import get_gardens

logger: logging.Logger = logging.getLogger(__name__)
conn_manager: Optional[StompManager] = None


def run(ep_conn):
    global conn_manager

    entry_config = config.get("entry.stomp")
    parent_config = config.get("parent.stomp")
    garden_name = config.get("garden.name")

    conn_manager = StompManager(ep_conn=ep_conn)

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


def signal_handler(_: int, __: types.FrameType):
    if conn_manager:
        conn_manager.stop()
