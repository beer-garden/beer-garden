import beer_garden.db.api as db


def get_namespaces():
    """
    Get the distinct namespaces in the Garden

    Returns:
        List

    """

    return db.distinct_namespaces()
