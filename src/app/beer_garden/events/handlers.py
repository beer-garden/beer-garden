# -*- coding: utf-8 -*-
import logging

from brewtils.models import Event, Events

import beer_garden.config
import beer_garden.garden
import beer_garden.router
import beer_garden.db.api as db
from beer_garden.local_plugins.manager import PluginManager

logger = logging.getLogger(__name__)


def garden_callbacks(event: Event) -> None:
    """Callbacks for events

    Args:
        event: The event

    Returns:
        None
    """

    if event.name in (Events.SYSTEM_CREATED.name, ):
        beer_garden.garden.garden_add_system(event.payload, event.garden)

        # Caches routing information
        beer_garden.router.update_system_mapping(event.payload, event.garden)

    if event.name in (Events.GARDEN_CREATED.name, Events.GARDEN_STARTED.name):
        beer_garden.router.update_garden_connection(event.payload)

    elif event.name in (Events.GARDEN_REMOVED.name, ):
        beer_garden.router.remove_garden_connection(event.payload)

    # Subset of events we only care about if they originate from the local garden
    if event.garden == beer_garden.config.get("garden.name"):
        if event.error:
            logger.error(f"Local error event ({event}): {event.error_message}")
            return

        try:
            # Start local plugins after the entry point comes up
            if event.name == Events.ENTRY_STARTED.name:
                PluginManager.instance().start_all()
            elif event.name == Events.INSTANCE_INITIALIZED.name:
                PluginManager.instance().associate(event)
            elif event.name == Events.INSTANCE_STARTED.name:
                PluginManager.instance().do_start(event)
            elif event.name == Events.INSTANCE_STOPPED.name:
                PluginManager.instance().do_stop(event)
        except Exception as ex:
            logger.exception(f"Error executing local callback for {event}: {ex}")

    # Subset of events we only care about if they originate from a downstream garden
    else:
        if event.error:
            logger.error(f"Downstream error event ({event}): {event.error_message}")
            return

        try:
            if event.name in (Events.REQUEST_CREATED.name, Events.SYSTEM_CREATED.name):
                db.create(event.payload)

            elif event.name in (
                Events.REQUEST_STARTED.name,
                Events.REQUEST_COMPLETED.name,
                Events.SYSTEM_UPDATED.name,
                Events.INSTANCE_UPDATED.name,
            ):
                db.update(event.payload)

            elif event.name in (Events.SYSTEM_REMOVED.name,):
                db.delete(event.payload)
        except Exception as ex:
            logger.exception(f"Error executing downstream callback for {event}: {ex}")
