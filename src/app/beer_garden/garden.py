# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from typing import List

from brewtils.errors import ModelValidationError, PluginError
from brewtils.models import Events, Garden, PatchOperation, System
import beer_garden.router


import beer_garden.db.api as db
from beer_garden.events import publish_event

logger = logging.getLogger(__name__)


def get_garden(garden_name: str) -> Garden:
    """Retrieve an individual Garden

    Args:
        garden_name: The name of Garden

    Returns:
        The Garden

    """
    return db.query_unique(Garden, name=garden_name)


def get_gardens() -> List[Garden]:
    """Retrieve list of all Gardens

    Returns:
        The Garden list

    """
    return db.query(Garden)


def update_garden_config(garden: Garden):
    db_garden = db.query_unique(Garden, id=garden.id)
    db_garden.connection_params = garden.connection_params
    db_garden.connection_type = garden.connection_type

    beer_garden.router.add_garden(db_garden)

    return update_garden(db_garden)


def update_garden_status(garden_name: str, new_status: str) -> Garden:
    """Update an Garden status.

    Will also update the status_info heartbeat.

    Args:
        garden_name: The Garden Name
        new_status: The new status

    Returns:
        The updated Garden
    """
    garden = db.query_unique(Garden, name=garden_name)
    garden.status = new_status
    garden.status_info["heartbeat"] = datetime.utcnow()

    update_garden(garden)
    logger.info("Downstream Namespace " + garden_name + " is now " + new_status)
    return garden


@publish_event(Events.GARDEN_REMOVED)
def remove_garden(garden_name: str) -> None:
    """Remove a garden

        Args:
            garden_name: The Garden name

        Returns:
            None

        """
    garden = db.query_unique(Garden, name=garden_name)
    db.delete(garden)
    return garden


@publish_event(Events.GARDEN_CREATED)
def create_garden(garden: Garden) -> Garden:
    """Create a new Garden

    Args:
        garden: The Garden to create

    Returns:
        The created Garden

    """

    garden.status = "INITIALIZING"
    garden.status_info["heartbeat"] = datetime.utcnow()
    db_garden = db.query_unique(Garden, name=garden.name)
    if db_garden:
        db_garden.status = garden.status
        db_garden.status_info = garden.status_info
        db_garden.connection_type = garden.connection_type
        db_garden.connection_params = garden.connection_params
        db_garden.namespaces = garden.namespaces
        db_garden.systems = garden.systems

        return db.update(db_garden)

    else:
        return db.create(garden)


def garden_add_system(system: System, garden_name: str):
    garden = get_garden(garden_name)

    if garden is None:
        raise PluginError(
            f"Garden '{garden_name}' does not exist, unable to map '{str(system)}"
        )

    if system.namespace not in garden.namespaces:
        garden.namespaces.append(system.namespace)

    if str(system) not in garden.systems:
        garden.systems.append(str(system))

    return update_garden(garden)


@publish_event(Events.GARDEN_UPDATED)
def update_garden(garden: Garden):
    return db.update(garden)
