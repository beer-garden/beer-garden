# -*- coding: utf-8 -*-
"""Package containing the Stomp entry point"""
import logging
import types

import beer_garden.config as config
from brewtils.models import Event, Events
from beer_garden.api.stomp.stomp_manager import StompManager
from beer_garden.events import publish
from beer_garden.garden import get_gardens

logger = logging.getLogger(__name__)
st_manager_stack = []


def run(ep_conn):
    global st_manager_stack
    entry_config = config.get("entry.stomp")
    parent_config = config.get("parent.stomp")

    if entry_config.get("enabled"):
        st_manager = StompManager(
            ep_conn=ep_conn,
            stomp_config=entry_config,
            name=f'{config.get("garden.name")}_entry',
        )
        if parent_config.get("enabled"):
            st_manager.add_connection(
                stomp_config=parent_config,
                name=f'{config.get("garden.name")}_parent',
                is_main=True,
            )
    elif parent_config.get("enabled"):
        st_manager = StompManager(
            ep_conn=ep_conn,
            stomp_config=parent_config,
            name=f'{config.get("garden.name")}_parent',
        )
    else:
        st_manager = StompManager(ep_conn=ep_conn)

    for garden in get_gardens(include_local=False):
        if garden.name != config.get("garden.name") and garden.connection_type:
            if garden.connection_type.casefold() == "stomp":
                connection_params = StompManager.format_connection_params(
                    "stomp_", garden.connection_params
                )
                connection_params["send_destination"] = None
                st_manager.add_connection(
                    stomp_config=connection_params, name=garden.name
                )

    st_manager.start()

    st_manager_stack.append(st_manager)
    logger.info("Stomp entry point started")

    publish(
        Event(name=Events.ENTRY_STARTED.name, metadata={"entry_point_type": "STOMP"})
    )


def signal_handler(_: int, __: types.FrameType):
    global st_manager_stack
    while st_manager_stack:
        st_manager_stack.pop().stop()
