# -*- coding: utf-8 -*-
import logging
from copy import deepcopy

from brewtils.models import Event

import beer_garden.config
import beer_garden.files
import beer_garden.garden
import beer_garden.local_plugins.manager
import beer_garden.log
import beer_garden.plugin
import beer_garden.requests
import beer_garden.router
import beer_garden.scheduler
import beer_garden.systems

logger = logging.getLogger(__name__)


def garden_callbacks(event: Event) -> None:
    """Callbacks for events

    Args:
        event: The event

    Returns:
        None
    """
    if event.error:
        logger.error(f"Error event: {event!r}")
        return
    else:
        logger.debug(f"{event!r}")

    # These are all the MAIN PROCESS subsystems that care about events
    for handler, handler_tag in [
        (beer_garden.application.handle_event, "Application"),
        (beer_garden.garden.handle_event, "Garden"),
        (beer_garden.plugin.handle_event, "Plugin"),
        (beer_garden.requests.handle_event, "Requests"),
        (beer_garden.requests.handle_wait_events, "Requests wait events"),
        (beer_garden.router.handle_event, "Router"),
        (beer_garden.systems.handle_event, "System"),
        (beer_garden.scheduler.handle_event, "Scheduler"),
        (beer_garden.log.handle_event, "Log"),
        (beer_garden.files.handle_event, "File"),
        (beer_garden.local_plugins.manager.handle_event, "Local plugins manager"),
    ]:
        try:
            handler(deepcopy(event))
        except Exception as ex:
            logger.error(
                "'%s' handler received an error executing callback for event %s: %s"
                % (handler_tag, repr(event), str(ex))
            )
