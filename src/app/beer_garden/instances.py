# -*- coding: utf-8 -*-
import logging

from brewtils.models import Events, Instance

import beer_garden.db.api as db
import beer_garden.config as config

logger = logging.getLogger(__name__)


def get_instance(instance_id: str = None, instance: Instance = None, **_) -> Instance:
    """Retrieve an individual Instance

    Args:
        instance_id: The Instance ID
        instance: The Instance

    Returns:
        The Instance

    """
    return instance or db.query_unique(Instance, id=instance_id)


def remove_instance(instance_id: str = None, instance: Instance = None, **_) -> None:
    """Removes an Instance

    Args:
        instance_id: The Instance ID
        instance: The Instance

    Returns:
        None
    """
    instance = instance or db.query_unique(Instance, id=instance_id)

    db.delete(instance)


def handle_event(event):
    # Only care about downstream garden
    if event.garden != config.get("garden.name"):

        if event.name == Events.INSTANCE_UPDATED.name:
            if not event.payload_type:
                logger.error(f"{event.name} error: no payload type ({event!r})")
                return

            record = db.query_unique(Instance, id=event.payload.id)

            if record:
                db.update(event.payload)
            else:
                logger.error(f"{event.name} error: object does not exist ({event!r})")
