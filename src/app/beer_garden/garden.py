# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from brewtils.errors import ModelValidationError, PluginError
from brewtils.models import Events, Garden, PatchOperation, System

import beer_garden.db.api as db
from beer_garden.events import publish_event

logger = logging.getLogger(__name__)


def get_garden(garden_name: str) -> Garden:
    """Retrieve an individual Garden

    Args:
        garden_name: The name of Garden

    Returns:
        The Namespace

    """
    return db.query_unique(Garden, garden_name=garden_name)


def update_garden(garden_name: str, patch: PatchOperation) -> Garden:
    """Applies updates to an Garden.

    Args:
        garden_name: The Garden Name
        patch: Patch definition to apply

    Returns:
        The updated Garden
    """
    garden = None

    for op in patch:
        operation = op.operation.lower()

        if operation in ["initializing", "running", "stopped", "block"]:
            garden = update_garden_status(garden_name, operation.upper())
        elif operation == "heartbeat":
            garden = update_garden_status(garden_name, "RUNNING")

        else:
            raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    return garden


def update_garden_status(garden_name: str, new_status: str) -> Garden:
    """Update an Garden status.

    Will also update the status_info heartbeat.

    Args:
        garden_name: The Garden Name
        new_status: The new status

    Returns:
        The updated Garden
    """
    garden = db.query_unique(Garden, garden_name=garden_name)
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
    garden = db.query_unique(Garden, garden_name=garden_name)
    db.delete(garden)


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
    db_garden = db.query_unique(Garden, garden_name=garden.name)
    if db_garden:
        db_garden.status = garden.status
        db_garden.status_info = garden.status_info
        db_garden.connection_type = garden.connection_type
        db_garden.connection_params = garden.connection_params

        db.update(garden)
    else:
        db.create(garden)

    return garden


def garden_add_namespace(system: System, garden_name: str):
    garden = get_garden(garden_name)

    if garden is None:
        raise PluginError(f"Garden '{garden_name}' does not exist, unable to map '{str(system)}")

    if system.namespace not in garden.namespaces:
        garden.namespaces.append(system.namespace)
        update_garden(garden)


@publish_event(Events.GARDEN_UPDATED)
def update_garden(garden: Garden):
    db.update(garden)

