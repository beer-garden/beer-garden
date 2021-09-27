from typing import Optional

from beer_garden.db.mongo.models import User


def get_user(request) -> Optional[User]:
    """Gets the User based on certificates supplied with in the request body

    Args:
        request: tornado HTTPServerRequest object

    Returns:
        User: The User object for the user specified by the certificates
        None: If no User was found
    """
    # This is currently just a stub and will be implemented in a future release
    return None
