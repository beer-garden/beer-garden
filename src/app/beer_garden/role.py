import logging
import os

import yaml
from brewtils.models import Event, Events, Permissions, Role
from mongoengine import DoesNotExist
from mongoengine.errors import FieldDoesNotExist

import beer_garden.db.api as db
from beer_garden import config
from beer_garden.events import publish_event

logger = logging.getLogger(__name__)


def create_role(role: Role) -> Role:
    """Create provided Role

    Args:
        role (Role): Role to create

    Returns:
        Role: Created Role
    """
    return db.create(role)


def get_role(role_name: str = None, role_id: str = None) -> Role:
    """Get Role from database

    Args:
        role_name (str, optional):  Role Name of Role to retrieve. Defaults to None.
        role_id (str, optional): Role Name of Role to retrieve. Defaults to None.

    Returns:
        Role: Requested Role
    """
    if role_name:
        return db.query_unique(Role, name=role_name, raise_missing=True)

    return db.query_unique(Role, id=role_id, raise_missing=True)


def get_roles():
    """Get all roles

    Returns:
        List[Role]: List of roles from database
    """
    return db.query(Role)


@publish_event(Events.ROLE_UPDATED)
def update_role(
    role: Role = None, role_name: str = None, role_id: str = None, **kwargs
) -> Role:
    """Updates provided Role

    Args:
        role (Role, optional): Role to update. Defaults to None.
        role_name (str, optional): Role Name of Role to update. Defaults to None.
        role_id (str, optional): Role ID of Role to update. Defaults to None.

    Returns:
        Role: Updated Role
    """
    if not role:
        if role_name:
            role = db.query_unique(Role, name=role_name, raise_missing=True)
        else:
            role = db.query_unique(Role, id=role_id, raise_missing=True)

    for key, value in kwargs.items():
        setattr(role, key, value)

    return db.update(role)


@publish_event(Events.ROLE_DELETED)
def delete_role(role: Role = None, role_name: str = None, role_id: str = None) -> Role:
    """Delete provided role

    Args:
        role (Role, optional): Role to delete. Defaults to None.
        role_name (str, optional): Role Name of Role to delete. Defaults to None.
        role_id (str, optional): Role Id of Role to delete. Defaults to None.

    Returns:
        Role: Deleted Role
    """
    if not role:
        if role_name:
            role = db.query_unique(Role, name=role_name, raise_missing=True)
        else:
            role = db.query_unique(Role, id=role_id, raise_missing=True)

    db.delete(role)

    return role


def load_roles_config():
    """Load local role definition file, if configured and exists"""
    if config.get("auth.role_definition_file"):
        if os.path.isfile(config.get("auth.role_definition_file")):
            with open(config.get("auth.role_definition_file"), "r") as config_file:
                return yaml.safe_load(config_file)
        else:
            logger.error(
                f"Unable to load Roles file: {config.get('auth.role_definition_file')}"
            )
    return []


def rescan():
    """Rescan the roles configuration file"""
    roles_config = load_roles_config()
    for role in roles_config:
        kwargs = {
            "name": role.get("name"),
            "permission": role.get("permission"),
            "description": role.get("description"),
            "scope_gardens": role.get("scope_gardens"),
            "scope_namespaces": role.get("scope_namespaces"),
            "scope_systems": role.get("scope_systems"),
            "scope_instances": role.get("scope_instances"),
            "scope_versions": role.get("scope_versions"),
            "scope_commands": role.get("scope_commands"),
            "file_generated": True,
            "protected": role.get("protected", False),
        }
        role = Role(**kwargs)
        try:
            existing = get_role(role.name)
            if existing:
                update_role(existing, **kwargs)
        except DoesNotExist:
            create_role(role)


def ensure_roles():
    """Create roles if necessary"""

    try:
        get_roles()
    except FieldDoesNotExist:
        logger.error("Legacy Role Models found, clearing collections")
        import beer_garden.db.mongo.models

        beer_garden.db.mongo.models.Role.drop_collection()

    configure_superuser_role()
    configure_plugin_role()
    rescan()


def configure_superuser_role():
    """Creates or updates the superuser role as needed"""
    try:
        superuser = get_role(role_name="superuser")
    except DoesNotExist:
        logger.info("Creating superuser role with all permissions")
        superuser = Role(
            name="superuser",
            description="Role containing max permissions",
            permission=Permissions.GARDEN_ADMIN.name,
            protected=True,
        )
        create_role(superuser)


def configure_plugin_role():
    """Creates or updates the plugin role as needed"""
    try:
        plugin_role = get_role(role_name="plugin")
    except DoesNotExist:
        logger.info("Creating plugin role with select permissions")
        plugin_role = Role(
            name="plugin",
            description="Role containing plugin permissions",
            permission="PLUGIN_ADMIN",
            protected=True,
        )
        create_role(plugin_role)


def handle_event(event: Event) -> None:
    """Processes the provided event by calling the correct handler function(s) for the
    given event type.

    Args:
        event: The Event to process

    Returns:
        None
    """
    return
