# -*- coding: utf-8 -*-
from typing import List

import brewtils.models
from brewtils.schema_parser import SchemaParser

from beer_garden.db.mongo.models import Command


def get_command(command_id: str) -> brewtils.models.Command:
    """Retrieve an individual Command

    Args:
        command_id: The Command ID

    Returns:
        The Command

    """
    return SchemaParser.parse_command(
        SchemaParser.serialize_command(
            Command.objects.get(id=command_id), to_string=False
        ),
        from_string=False,
    )


def get_commands() -> List[brewtils.models.Command]:
    """Retrieve all Commands

    Returns:
        The Commands

    """
    return SchemaParser.parse_command(
        SchemaParser.serialize_command(
            Command.objects.all(), to_string=False, many=True
        ),
        from_string=False,
        many=True,
    )
