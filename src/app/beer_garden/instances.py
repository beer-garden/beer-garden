# -*- coding: utf-8 -*-
import logging

from brewtils.errors import BrewtilsException
from brewtils.models import Events, Instance, System

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.errors import NotFoundException

logger = logging.getLogger(__name__)


def get_instance(
    instance_id: str = None,
    system_id: str = None,
    instance_name: str = None,
    instance: Instance = None,
    **_,
) -> Instance:
    """Retrieve an individual Instance

    Args:
        instance_id: The Instance ID
        system_id: The System ID
        instance_name: The Instance name
        instance: The Instance

    Returns:
        The Instance

    """
    if instance:
        return instance

    if system_id and instance_name:
        system = db.query_unique(System, raise_missing=True, id=system_id)

        try:
            return system.get_instance_by_name(instance_name, raise_missing=True)
        except BrewtilsException:
            raise NotFoundException(
                f"System {system} does not have an instance with name '{instance_name}'"
            ) from None

    elif instance_id:
        system = db.query_unique(System, raise_missing=True, instances__id=instance_id)

        try:
            return system.get_instance_by_id(instance_id, raise_missing=True)
        except BrewtilsException:
            raise NotFoundException(
                f"System {system} does not have an instance with id '{instance_id}'"
            ) from None

    raise NotFoundException()


def remove_instance(
    *_, system: System = None, instance: Instance = None, **__
) -> Instance:
    """Removes an Instance

    Args:
        system: The System
        instance: The Instance

    Returns:
        The deleted Instance
    """
    db.modify(system, pull__instances=instance)

    return instance


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
