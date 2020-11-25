from typing import List
from brewtils.models import Role

import beer_garden.db.api as db


def get_roles(**kwargs) -> List[Role]:
    """Search for Requests

    Args:
        kwargs: Parameters to be passed to the DB query

    Returns:
        The list of Requests that matched the query

    """
    return db.query(Role, **kwargs)
