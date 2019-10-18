# -*- coding: utf-8 -*-
from typing import List

from brewtils.models import Command

from beer_garden.db.api import query_unique, query


def get_command(command_id: str) -> Command:
    """Retrieve an individual Command

    Args:
        command_id: The Command ID

    Returns:
        The Command

    """
    return query_unique(Command, id=command_id)


def get_commands() -> List[Command]:
    """Retrieve all Commands

    Returns:
        The Commands

    """
    return query(Command)
