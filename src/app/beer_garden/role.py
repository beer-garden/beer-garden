import logging
from typing import List

from brewtils.models import Event as BrewtilsEvent
from marshmallow import Schema, fields
from mongoengine import DoesNotExist

from beer_garden import config
from beer_garden.db.mongo.models import Garden, RemoteRole, Role, User

logger = logging.getLogger(__name__)


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
    # Avoid circular import
    from beer_garden.user import update_user

    impacted_users = User.objects.filter(role_assignments__match={"role": role})
    total_removed_count = 0

    for user in impacted_users:
        prev_role_assignment_count = len(user.role_assignments)

        role_assignments = list(
            filter(lambda ra: ra.role != role, user.role_assignments)
        )
        update_user(user, role_assignments=role_assignments)

        total_removed_count += prev_role_assignment_count - len(user.role_assignments)

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

            if role_obj.protected:
                logger.info(
                    "Role sync request for protected role %s will be ignored.",
                    role_obj.name,
                )
                continue

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

    roles_to_remove = Role.objects.filter(name__nin=role_names, protected__ne=True)

    for role in roles_to_remove:
        remove_role(role)

    return len(roles_to_remove)


def _role_synced_with_garden(role: Role, garden: Garden) -> bool:
    """Checks if the supplied role is currently synced to the supplied garden, based
    on the corresponding RemoteRole entry. A role is considered synced if there is a
    RemoteRole entry for the specified garden and the permissions and description of
    that entry match those of the Role.

    Args:
        role: The role for which we are checking the sync status
        garden: The remote garden to check the status against

    Returns:
        bool: True if the role is currently synced. False otherwise.
    """
    try:
        remote_role = RemoteRole.objects.get(name=role.name, garden=garden.name)
    except RemoteRole.DoesNotExist:
        return False

    return (set(role.permissions) == set(remote_role.permissions)) and (
        role.description == remote_role.description
    )


def role_sync_status(roles: List[Role]) -> dict:
    """Provides the sync status of the provided Role with each remote garden. The
    resulting dict formatting is:

    {
        "role_name": {
            "remote_garden_name": bool,
            "remote_garden_name": bool,
        }
    }

    Args:
        roles: The roles for which we are checking the sync status

    Returns:
        dict: Sync status by role name and garden name
    """
    sync_status = {}

    for garden in Garden.objects.filter(connection_type__nin=["LOCAL"]):
        for role in roles:
            if role.name not in sync_status:
                sync_status[role.name] = {}

            sync_status[role.name][garden.name] = _role_synced_with_garden(role, garden)

    return sync_status


def handle_event(event: BrewtilsEvent) -> None:
    """Processes the provided event by calling the correct handler function(s) for the
    given event type.

    Args:
        event: The BrewtilsEvent to process

    Returns:
        None
    """
    # Only handle events from downstream gardens
    if event.garden == config.get("garden.name"):
        return

    if event.name == "ROLE_UPDATED":
        _handle_role_updated_event(event)


def _handle_role_updated_event(event: BrewtilsEvent) -> None:
    """Handling for ROLE_UPDATED events"""
    # NOTE: This event stores its data in the metadata field as a workaround to the
    # brewtils models dependency inherent in the more typical event publishing flow
    try:
        garden = event.metadata["garden"]
        updated_role = event.metadata["role"]
        name = updated_role["name"]

        try:
            remote_role = RemoteRole.objects.get(garden=garden, name=name)
        except RemoteRole.DoesNotExist:
            remote_role = RemoteRole(garden=garden, name=name)

        remote_role.permissions = updated_role.get("permissions")
        remote_role.description = updated_role.get("description")
        remote_role.updated_at = event.timestamp
        remote_role.save()
    except KeyError:
        logger.error("Error parsing %s event from garden %s", event.name, event.garden)
