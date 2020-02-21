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
    return list(
        set(db.distinct(Request, "namespace"))
        | set(db.distinct(System, "namespace"))
        # set(db.distinct(Garden, "namespaces"))
    )
