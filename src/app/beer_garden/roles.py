from typing import List

from brewtils.errors import ModelValidationError
from brewtils.models import Role, Permission

import beer_garden.db.api as db


def get_role(role_id: str = None, username: str = None):
    if role_id:
        return db.query_unique(Role, id=role_id)
    else:
        return db.query_unique(Role, username=username)


def get_roles(**kwargs) -> List[Role]:
    """Search for Roles

    Args:
        kwargs: Parameters to be passed to the DB query

    Returns:
        The list of Roles that matched the query

    """
    return db.query(Role, **kwargs)


def create_role(role: Role):
    return db.create(role)


def delete_role(role_id: str = None, role: Role = None):
    role = role or db.query_unique(Role, id=role_id)

    if role.name in ("bg-admin", "bg-anonymous", "bg-plugin"):
        raise ModelValidationError("Unable to remove '%s' role" % role.name)

    db.delete(role)

    return role


def update_permission(role_id: str = None, permission: Permission = None):
    role = db.query_unique(Role, id=role_id)

    updates = dict()

    updates["permissions"] = list()

    for original_permission in role.permissions:
        if original_permission.namespace != permission.namespace:
            updates["permissions"].append(db.from_brewtils(original_permission))

    updates["permissions"].append(db.from_brewtils(permission))

    role = db.modify(role, **updates)

    return role


def remove_permission(role_id: str = None, permission: Permission = None):
    role = db.query_unique(Role, id=role_id)

    role.permissions
    updates = dict()

    updates["permissions"] = list()

    for original_permission in role.permissions:
        if original_permission.namespace != permission.namespace:
            updates["permissions"].append(db.from_brewtils(original_permission))

    role = db.modify(role, **updates)

    return role


def update_description(role_id: str = None, description: str = None):
    role = db.query_unique(Role, id=role_id)

    updates = dict()
    updates["description"] = description

    role = db.modify(role, **updates)

    return role
