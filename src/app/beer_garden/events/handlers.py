# -*- coding: utf-8 -*-
import logging

from brewtils.models import Event, Events

import beer_garden.config
import beer_garden.db.api as db
from beer_garden.local_plugins.manager import PluginManager

logger = logging.getLogger(__name__)


def local_callbacks(event: Event) -> None:
    """Callbacks for events originating from the local garden

    Args:
        event: The event

    Returns:
        None
    """
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


def downstream_callbacks(event: Event) -> None:
    """Callbacks for events originating from downstream gardens

    Args:
        event: The event

    Returns:
        None
    """
    if event.garden != beer_garden.config.get("garden.name"):
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
