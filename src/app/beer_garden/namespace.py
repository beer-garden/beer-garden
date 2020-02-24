# -*- coding: utf-8 -*-
from typing import List

from brewtils.models import Garden, Request, System

import beer_garden.db.api as db


def get_namespaces() -> List[str]:
    """
    Get the distinct namespaces in the Garden

    Returns:
        List

    """
    namespaces = set(
        set(db.distinct(Request, "namespace")) | set(db.distinct(System, "namespace"))
    )

    for garden in db.query(Garden, include_fields="namespaces"):
        namespaces |= set(garden.namespaces)

    return list(namespaces)
