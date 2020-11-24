# -*- coding: utf-8 -*-
"""Commands Service

The config service is responsible for:

* Retrieving single `Command` objects
* Generating list of all `System` `Commands`
"""

import itertools
from typing import List

from brewtils.models import Command, System

import beer_garden.db.api as db


def get_command(system_id: str, command_name: str) -> Command:
    """Retrieve an individual Command

    Args:
        system_id: The System ID
        command_name: The Command name

    Returns:
        The Command

    """
    system = db.query_unique(
        System, raise_missing=True, id=system_id, commands__name=command_name
    )

    for command in system.commands:
        if command.name == command_name:
            return command


def get_commands() -> List[Command]:
    """Retrieve all Commands

    Returns:
        The Commands

    """
    commands_list = [system.commands for system in db.query(System)]

    return list(itertools.chain.from_iterable(commands_list))
