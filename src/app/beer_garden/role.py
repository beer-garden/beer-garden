import logging
import yaml
from typing import List

# from brewtils.models import Event as BrewtilsEvent
from brewtils.models import Role, Event
from mongoengine import DoesNotExist
# from marshmallow import Schema, fields
# from mongoengine import DoesNotExist

from beer_garden import config
import beer_garden.db.api as db
#from beer_garden.db.mongo.models import Garden, RemoteRole, Role, User
# from beer_garden.user import update_user
logger = logging.getLogger(__name__)



def create_role(role: Role) -> Role:
    return db.create(role)

def get_role(role_name: str = None, role_id: str = None):
    if role_name:
        return db.query_unique(Role, name=role_name, raise_missing=True)
    
    return db.query_unique(Role, id=role_id, raise_missing=True)

def get_roles():
    return db.query(Role)

def update_role(role: Role = None, role_name: str = None, role_id: str = None,  **kwargs) -> Role:
    
    if not role:
        if role_name:
            role = db.query_unique(Role, name=role_name, raise_missing=True)
        else:
            role = db.query_unique(Role, id=role_id, raise_missing=True)

    for key, value in kwargs.items():
        setattr(role, key, value)

    return db.update(role)

# @publish_event(Events.ROLE_DELETE)
def delete_role(role: Role = None, role_name: str = None, role_id: str = None) -> Role:
    if not role:
        if role_name:
            role = db.query_unique(Role, name=role_name, raise_missing=True)
        else:
            role = db.query_unique(Role, id=role_id, raise_missing=True)

    #remove_local_role_assignments_for_role(role)

    db.delete(role)

    return role

def load_roles_config():
    with open(config.get("auth.role_definition_file"), "r") as config_file:
        return yaml.safe_load(config_file)

def rescan():
    """ Rescan the roles configuration file"""
    roles_config = load_roles_config()
    for role in roles_config:
        kwargs = {"name": role.get("name"), 
                  "permission": role.get("permission"),
                  "description": role.get("description"),
                  "scope_gardens": role.get("scope_gardens"),
                  "scope_namespaces": role.get("scope_namespaces"),
                  "scope_systems": role.get("scope_systems"),
                  "scope_instances": role.get("scope_instances"),
                  "scope_versions": role.get("scope_versions"),
                  "scope_commands": role.get("scope_commands")}
        role = Role(**kwargs)
        try:
            existing = get_role(role.name)
            if existing:
                update_role(existing, **kwargs)
        except DoesNotExist:
            create_role(role)

def ensure_roles():
    """Create roles if necessary"""
    configure_superuser_role()
    configure_plugin_role()
    rescan()

def configure_superuser_role():
    """Creates or updates the superuser role as needed"""
    try:
        superuser = get_role(role_name="superuser")
    except DoesNotExist:
        logger.info("Creating superuser role with all permissions")
        superuser = Role(name="superuser", description = "Role containing max permissions", permission="GARDEN_ADMIN")
        create_role(superuser)

def configure_plugin_role():
    """Creates or updates the plugin role as needed"""
    try:
        plugin_role = get_role(role_name="plugin")
    except DoesNotExist:
        logger.info("Creating plugin role with select permissions")
        plugin_role = Role(name="plugin", description = "Role containing plugin permissions", permission="PLUGIN_ADMIN")
        create_role(plugin_role)


#Old Stuff
################################





# def sync_roles(role_sync_data: list):
#     """Syncs the Roles in the database with a provided role list.

#     Args:
#         role_sync_data: A list of dictionaries containing role data. See RoleSyncSchema
#             for the expected format.

#     Returns:
#         None
#     """
#     roles = RoleSyncSchema(strict=True).load(role_sync_data, many=True).data

#     _delete_roles_not_in_list(roles)

#     for role in roles:
#         try:
#             role_obj = Role.objects.get(name=role["name"])

#             if role_obj.protected:
#                 logger.info(
#                     "Role sync request for protected role %s will be ignored.",
#                     role_obj.name,
#                 )
#                 continue

#             role_obj.description = role["description"]
#             role_obj.permissions = role["permissions"]
#         except DoesNotExist:
#             role_obj = Role(**role)

#         role_obj.save()


# def _delete_roles_not_in_list(roles: list) -> int:
#     """Delete all Roles in the database not represented in the provided list by name.

#     Args:
#        roles: A list of dictionaries containing role data. Any role not present
#          in the list will be deleted.

#     Returns:
#         int: The number of roles deleted
#     """
#     role_names = [role["name"] for role in roles]

#     roles_to_remove = Role.objects.filter(name__nin=role_names, protected__ne=True)

#     for role in roles_to_remove:
#         remove_role(role)

#     return len(roles_to_remove)


# def _role_synced_with_garden(role: Role, garden: Garden) -> bool:
#     """Checks if the supplied role is currently synced to the supplied garden, based
#     on the corresponding RemoteRole entry. A role is considered synced if there is a
#     RemoteRole entry for the specified garden and the permissions and description of
#     that entry match those of the Role.

#     Args:
#         role: The role for which we are checking the sync status
#         garden: The remote garden to check the status against

#     Returns:
#         bool: True if the role is currently synced. False otherwise.
#     """
#     try:
#         remote_role = RemoteRole.objects.get(name=role.name, garden=garden.name)
#     except RemoteRole.DoesNotExist:
#         return False

#     return (set(role.permissions) == set(remote_role.permissions)) and (
#         role.description == remote_role.description
#     )


# def role_sync_status(roles: List[Role]) -> dict:
#     """Provides the sync status of the provided Role with each remote garden. The
#     resulting dict formatting is:

#     {
#         "role_name": {
#             "remote_garden_name": bool,
#             "remote_garden_name": bool,
#         }
#     }

#     Args:
#         roles: The roles for which we are checking the sync status

#     Returns:
#         dict: Sync status by role name and garden name
#     """
#     sync_status = {}

#     for garden in Garden.objects.filter(connection_type__nin=["LOCAL"]):
#         for role in roles:
#             if role.name not in sync_status:
#                 sync_status[role.name] = {}

#             sync_status[role.name][garden.name] = _role_synced_with_garden(role, garden)

#     return sync_status


def handle_event(event: Event) -> None:
    """Processes the provided event by calling the correct handler function(s) for the
    given event type.

    Args:
        event: The Event to process

    Returns:
        None
    """
    return
#     # Only handle events from downstream gardens
#     if event.garden == config.get("garden.name"):
#         return

#     if event.name == "ROLE_UPDATED":
#         _handle_role_updated_event(event)


# def _handle_role_updated_event(event: BrewtilsEvent) -> None:
#     """Handling for ROLE_UPDATED events"""
#     # NOTE: This event stores its data in the metadata field as a workaround to the
#     # brewtils models dependency inherent in the more typical event publishing flow
#     try:
#         garden = event.metadata["garden"]
#         updated_role = event.metadata["role"]
#         name = updated_role["name"]

#         try:
#             remote_role = RemoteRole.objects.get(garden=garden, name=name)
#         except RemoteRole.DoesNotExist:
#             remote_role = RemoteRole(garden=garden, name=name)

#         remote_role.permissions = updated_role.get("permissions")
#         remote_role.description = updated_role.get("description")
#         remote_role.updated_at = event.timestamp
#         remote_role.save()
#     except KeyError:
#         logger.error("Error parsing %s event from garden %s", event.name, event.garden)
