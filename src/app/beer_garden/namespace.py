# -*- coding: utf-8 -*-
"""Namespace Service

The namespace service is responsible for
* Providing the default namespace from config
* Providing list of all known namespaces
"""

from typing import List, Optional

from mongoengine import QuerySet

import beer_garden.config as config
from beer_garden.db.mongo.models import Garden, Request, System


def default() -> str:
    """Get the default namespace for this Garden

    Returns:
        The default namespace
    """
    return config.get("garden.name")


def get_namespaces(
    garden_queryset: Optional[QuerySet] = None,
    system_queryset: Optional[QuerySet] = None,
    request_queryset: Optional[QuerySet] = None,
) -> List[str]:
    """Get the distinct namespaces in the Garden

    Returns:
        List
    """
    gardens = garden_queryset or Garden.objects
    systems = system_queryset or System.objects
    requests = request_queryset or Request.objects

    namespaces = set()
    namespaces |= set(requests.distinct("namespace"))
    namespaces |= set(systems.distinct("namespace"))

    for garden in gardens.only("namespaces"):
        namespaces |= set(garden.namespaces)

    # Filter out None, empty string
    namespaces = filter(lambda x: x, namespaces)

    return list(namespaces)
