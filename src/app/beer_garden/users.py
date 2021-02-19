from typing import List

import beer_garden.db.api as db
from brewtils.models import Principal, Role


def get_user(user_id: str = None, username: str = None):
    if user_id:
        return db.query_unique(Principal, id=user_id)
    if username:
        return db.query_unique(Principal, username=username)


def get_users(**kwargs) -> List[Principal]:
    """Search for Principals

    Args:
        kwargs: Parameters to be passed to the DB query

    Returns:
        The list of Principal that matched the query

    """
    return db.query(Principal, **kwargs)


def create_user(username: str = None, roles: list = None, password_hash: str = None):
    new_roles = [db.query_unique(Role, name=name) for name in roles]

    principal = Principal(username=username, roles=new_roles)

    principal = db.create(principal)

    return update_user(principal=principal, updates={"hash": password_hash})


def delete_user(user_id: str = None, principal: Principal = None):
    principal = principal or db.query_unique(Principal, id=user_id)

    db.delete(principal)

    return principal


def update_user(
    user_id: str = None, principal: Principal = None, updates: dict = dict()
):
    principal = principal or db.query_unique(Principal, id=user_id)

    principal = db.modify(principal, **updates)

    return principal


def update_roles(user_id: str = None, role_id: str = None):
    principal = db.query_unique(Principal, id=user_id)

    updates = dict()

    updates["roles"] = list()

    for original_roles in principal.roles:
        if original_roles.id != role_id:
            updates["roles"].append(db.from_brewtils(original_roles))

    new_role = db.query_unique(Role, id=role_id)
    updates["roles"].append(db.from_brewtils(new_role))

    return update_user(principal=principal, updates=updates)


def remove_role(user_id: str = None, role_id: str = None):
    principal = db.query_unique(Principal, id=user_id)

    updates = dict()

    updates["roles"] = list()

    for original_roles in principal.roles:
        if original_roles.id != role_id:
            updates["roles"].append(db.from_brewtils(original_roles))

    return update_user(principal=principal, updates=updates)


def coalesce_permissions(role_list):
    """Determine permissions"""

    if not role_list:
        return set(), list()

    aggregate_roles = set()
    aggregate_perms = list()

    for role in role_list:
        aggregate_roles.add(role.name)

        for permission in role.permissions:
            unmatched = True

            for index, agg_perm in enumerate(aggregate_perms):
                if (
                    agg_perm.namespace == permission.namespace
                    and agg_perm.garden == permission.garden
                ):
                    unmatched = False
                    if agg_perm.access == "READ" and permission.access in [
                        "ADMIN",
                        "OPERATOR",
                    ]:
                        aggregate_perms[index] = permission
                    elif agg_perm.access == "OPERATOR" and permission.access in [
                        "ADMIN"
                    ]:
                        aggregate_perms[index] = permission
                    break

            if unmatched:
                aggregate_perms.append(permission)

    return aggregate_roles, aggregate_perms
