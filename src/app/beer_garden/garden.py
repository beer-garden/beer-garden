# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from beer_garden.errors import RoutingRequestException
from beer_garden.router import Route_Type
from brewtils.errors import ModelValidationError
from brewtils.models import Events, Garden, PatchOperation, System


import beer_garden.db.api as db
from beer_garden.events.events_manager import publish_event

logger = logging.getLogger(__name__)


def route_request(
    brewtils_obj=None, obj_id: str = None, route_type: Route_Type = None, **kwargs
):
    if route_type is Route_Type.CREATE:
        if brewtils_obj is None:
            raise RoutingRequestException(
                "An Object is required to route CREATE request for Garden"
            )

        return create_garden(brewtils_obj)
    elif route_type is Route_Type.READ:
        if obj_id is None:
            raise RoutingRequestException(
                "An identifier is required to route READ request for Garden"
            )

        return get_garden(obj_id)
    elif route_type is Route_Type.UPDATE:
        if obj_id is None or brewtils_obj is None:
            raise RoutingRequestException(
                "An identifier and Object are required to route UPDATE request for Garden"
            )

        return update_garden(obj_id, brewtils_obj)
    elif route_type is Route_Type.DELETE:
        if obj_id is None:
            raise RoutingRequestException(
                "An identifier is required to route DELETE request for Garden"
            )

        return remove_garden(obj_id)
    else:
        raise RoutingRequestException(
            "%s Route for Garden does not exist" % route_type.value
        )


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


@publish_event(Events.GARDEN_UPDATED)
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

    garden = db.update(garden)
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
    db_garden = db.query_unique(Garden, garden_name=garden.garden_name)
    if db_garden:
        db_garden.status = garden.status
        db_garden.status_info = garden.status_info
        db_garden.connection_type = garden.connection_type
        db_garden.connection_params = garden.connection_params

        garden = db.update(db_garden)
    else:
        garden = db.create(garden)

    return garden
