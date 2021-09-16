from marshmallow import Schema, fields
from mongoengine import DoesNotExist

from beer_garden.db.mongo.models import Role, User


class RoleSyncSchema(Schema):
    """Role syncing input schema"""

    name = fields.Str(required=True)
    description = fields.Str(allow_none=True, missing=None)
    permissions = fields.List(fields.Str(), required=True)


def remove_role(role: Role):
    """Remove a Role. This will also remove any references to the Role, such as those
    in User role assignments.

    Args:
        role: The Role document object.

    Returns:
        None
    """
    remove_role_assignments_for_role(role)
    role.delete()


def remove_role_assignments_for_role(role: Role) -> int:
    """Remove all User role assignments for the provided Role.

    Args:
        role: The Role document object

    Returns:
        int: The number of role assignments removed
    """
    impacted_users = User.objects.filter(role_assignments__match={"role": role})
    total_removed_count = 0

    for user in impacted_users:
        prev_role_assignment_count = len(user.role_assignments)

        user.role_assignments = list(
            filter(lambda ra: ra.role != role, user.role_assignments)
        )

        total_removed_count += prev_role_assignment_count - len(user.role_assignments)

        user.save()

    return total_removed_count


def sync_roles(role_sync_data: list):
    """Syncs the Roles in the database with a provided role list.

    Args:
        role_sync_data: A list of dictionaries containing role data. See RoleSyncSchema
            for the expected format.

    Returns:
        None
    """
    roles = RoleSyncSchema(strict=True).load(role_sync_data, many=True).data

    _delete_roles_not_in_list(roles)

    for role in roles:
        try:
            role_obj = Role.objects.get(name=role["name"])
            role_obj.description = role["description"]
            role_obj.permissions = role["permissions"]
        except DoesNotExist:
            role_obj = Role(**role)

        role_obj.save()


def _delete_roles_not_in_list(roles: list) -> int:
    """Delete all Roles in the database not represented in the provided list by name.

    Args:
       roles: A list of dictionaries containing role data. Any role not present
         in the list will be deleted.

    Returns:
        int: The number of roles deleted
    """
    role_names = [role["name"] for role in roles]

    roles_to_remove = Role.objects.filter(name__nin=role_names)

    for role in roles_to_remove:
        remove_role(role)

    return len(roles_to_remove)
