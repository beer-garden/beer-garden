# -*- coding: utf-8 -*-
from typing import List

from beer_garden.errors import RoutingRequestException
from beer_garden.router import Route_Type
from brewtils.models import Command

import beer_garden.db.api as db


def route_request(obj_id: str = None, route_type: Route_Type = None, **kwargs):
    if route_type is Route_Type.CREATE:
        raise RoutingRequestException("CREATE Route for Commands does not exist")
    elif route_type is Route_Type.READ:
        if obj_id:
            return get_command(obj_id)
        else:
            return get_commands()
    elif route_type is Route_Type.UPDATE:
        raise RoutingRequestException("UPDATE Route for Commands does not exist")
    elif route_type is Route_Type.DELETE:
        raise RoutingRequestException("DELETE Route for Commands does not exist")


def get_command(command_id: str) -> Command:
    """Retrieve an individual Command

    Args:
        command_id: The Command ID

    Returns:
        The Command

    """
    return db.query_unique(Command, id=command_id)


def get_commands() -> List[Command]:
    """Retrieve all Commands

    Returns:
        The Commands

    """
    return db.query(Command)
