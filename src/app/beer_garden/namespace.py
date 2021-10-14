# -*- coding: utf-8 -*-
"""Namespace Service

The namespace service is responsible for
* Providing the default namespace from config
* Providing list of all known namespaces
"""

from typing import List

from brewtils.models import Garden, Request, System

import beer_garden.config as config
import beer_garden.db.api as db


def default() -> str:
    """Get the default namespace for this Garden

    Returns:
        The default namespace
    """
    return config.get("garden.name")


def get_namespaces() -> List[str]:
    """Get the distinct namespaces in the Garden

    Returns:
        List

    """
    namespaces = set(
        set(db.distinct(Request, "namespace")) | set(db.distinct(System, "namespace"))
    )

    for garden in db.query(Garden, include_fields=["namespaces"]):
        namespaces |= set(garden.namespaces)

    # Filter out None, empty string
    namespaces = filter(lambda x: x, namespaces)

    return list(namespaces)
