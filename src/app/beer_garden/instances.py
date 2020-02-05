# -*- coding: utf-8 -*-
import logging

from brewtils.models import Instance

import beer_garden.db.api as db
from beer_garden.errors import RoutingRequestException
from beer_garden.router import Route_Type

logger = logging.getLogger(__name__)


def route_request(
    brewtils_obj=None, obj_id: str = None, route_type: Route_Type = None, **kwargs
):
    if route_type is Route_Type.CREATE:
        raise RoutingRequestException("CREATE Route for Instances does not exist")
    elif route_type is Route_Type.READ:
        if obj_id is None:
            raise RoutingRequestException(
                "An identifier is required to route READ request for Instances"
            )
        return get_instance(obj_id)
    elif route_type is Route_Type.DELETE:
        if obj_id is None:
            raise RoutingRequestException(
                "An identifier is required to route DELETE request for Instances"
            )
        return remove_instance(obj_id)
    else:
        raise RoutingRequestException(
            "%s Route for Instances does not exist" % route_type.value
        )


def get_instance(instance_id: str) -> Instance:
    """Retrieve an individual Instance

    Args:
        instance_id: The Instance ID

    Returns:
        The Instance

    """
    return db.query_unique(Instance, id=instance_id)


def remove_instance(instance_id: str) -> None:
    """Removes an Instance

    Args:
        instance_id: The Instance ID

    Returns:
        None
    """
    db.delete(db.query_unique(Instance, id=instance_id))
