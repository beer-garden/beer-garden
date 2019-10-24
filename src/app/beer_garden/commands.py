# -*- coding: utf-8 -*-
from typing import List

from brewtils.models import Command

import beer_garden.db.api as db


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
