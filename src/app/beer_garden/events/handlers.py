# -*- coding: utf-8 -*-
import logging
from brewtils.models import Event

import beer_garden.config
import beer_garden.garden
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
    for handler in [
        beer_garden.application.handle_event,
        beer_garden.garden.handle_event,
        beer_garden.plugin.handle_event,
        beer_garden.requests.handle_event,
        beer_garden.router.handle_event,
        beer_garden.systems.handle_event,
        beer_garden.scheduler.handle_event,
        beer_garden.log.handle_event,
    ]:
        try:
            handler(event)
        except Exception as ex:
            logger.exception(f"Error executing callback for {event!r}: {ex}")
