from typing import List

import beer_garden.db.api as db
from brewtils.models import Principal, Role


def get_user(user_id: str = None):
    return db.query_unique(Principal, id=user_id)


def get_users(**kwargs) -> List[Principal]:
    """Search for Principals

    Args:
        kwargs: Parameters to be passed to the DB query

    Returns:
        The list of Principal that matched the query

    """
    return db.query(Principal, **kwargs)


def create_user(principal: Principal):
    return db.create(principal)


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
                if agg_perm.namespace == permission.namespace:
                    unmatched = False
                    if agg_perm.access == "READ" and permission.access in [
                        "ADMIN",
                        "MAINTAINER",
                        "CREATE",
                    ]:
                        aggregate_perms[index] = permission
                    elif agg_perm.access == "CREATE" and permission.access in [
                        "ADMIN",
                        "MAINTAINER",
                    ]:
                        aggregate_perms[index] = permission
                    elif agg_perm.access == "MAINTAINER" and permission.access in [
                        "ADMIN"
                    ]:
                        aggregate_perms[index] = permission
                    break

            if unmatched:
                aggregate_perms.append(permission)

    return aggregate_roles, aggregate_perms
