import logging
from copy import deepcopy

import yaml
from brewtils.models import Event, Events, Garden, Operation, Role, User, UserToken
from brewtils.schema_parser import SchemaParser
from mongoengine import DoesNotExist
from passlib.apps import custom_app_context

import beer_garden.db.api as db
from beer_garden import config

# from beer_garden.role import RoleSyncSchema, role_sync_status, sync_roles
from beer_garden.errors import ConfigurationError, InvalidPasswordException
from beer_garden.events import publish
from beer_garden.garden import get_garden, get_gardens
from beer_garden.role import get_role

logger = logging.getLogger(__name__)

"""
User Actions should never throw Events. These events get broadcasted to the UI. This
could cause issues in scenarios where a child garden has authentication and the parent
does not. Where anyone monitoring the parent events could see unfiltered user updates
on child.
"""


def set_password(user: User, password: str = None):
    """This helper should be used to set the user's password, rather than directly
    assigning a value. This ensures that the password is stored as a hash rather
    than in plain text

    Args:
        password: String to set as the user's password.

    Returns:
        None
    """
    user.password = custom_app_context.hash(password or user.password)


def verify_password(user: User, password: str):
    """Checks the provided plaintext password against thea user's stored password
    hash

    Args:
        password: Plaintext string to check against user's password"

    Returns:
        bool: True if the password matches, False otherwise
    """
    return custom_app_context.verify(password, user.password)


def create_token(token: UserToken):
    """ """
    return db.create(token)


def get_token(uuid: str):
    """ """
    return db.query_unique(UserToken, uuid=uuid, raise_missing=True)


def delete_token(token: UserToken):
    """ """
    return db.delete(token)


def has_token(username: str):
    return db.count(UserToken, username=username) > 0


def revoke_tokens(user: User = None, username: str = None) -> None:
    """Remove all tokens from the user's list of valid tokens. This is useful for
    requiring the user to explicitly login, which one may want to do for a variety
    of reasons.
    """
    for user_token in db.query(
        UserToken, filter_params={"username": user.username if user else username}
    ):
        db.delete(user_token)


def validated_token_ttl():
    for ttl in ["garden_admin", "plugin_admin", "operator", "read_only"]:
        if config.get(f"auth.token_access_ttl.{ttl}") > config.get(
            f"auth.token_refresh_ttl.{ttl}"
        ):
            raise ConfigurationError(
                f"Refresh Token TTL {ttl} expires prior to Access Token TTL {ttl}"
            )


def get_user(username: str = None, id: str = None, include_roles: bool = True) -> User:
    """ """
    if username:
        user = db.query_unique(User, username=username, raise_missing=True)
    else:
        user = db.query_unique(User, id=id, raise_missing=True)
    if include_roles:
        for role in user.roles:
            user.local_roles.append(get_role(role))

    return user


def get_users() -> list:
    users = db.query(User)
    for user in users:
        for role in user.roles:
            user.local_roles.append(get_role(role))

        user.metadata["has_token"] = has_token(user.username)
    return users


def load_users_config():
    if config.get("auth.user_definition_file"):
        with open(config.get("auth.user_definition_file"), "r") as config_file:
            return yaml.safe_load(config_file)
    return []


def rescan():
    """Recan the users config"""
    users_config = load_users_config()
    for user in users_config:
        kwargs = {
            "username": user.get("username"),
            "roles": user.get("roles"),
            "file_generated": True,
            "protected": user.get("protected", False),
        }
        user = User(**kwargs)
        try:
            existing = get_user(user.username)
            if existing:
                update_user(existing, **kwargs)
        except DoesNotExist:
            create_user(user)


def create_user(user: User) -> User:
    """Creates a User using the provided kwargs. The created user is saved to the
    database and returned.

    Args:
        **kwargs: Keyword arguments accepted by the User __init__

    Returns:
        User: The created User instance
    """

    if user.password:
        set_password(user)

    user = db.create(user)
    user.local_roles = []
    for role in user.roles:
        user.local_roles.append(get_role(role))

    # Sync child gardens
    initiate_user_sync()

    return user


def delete_user(username: str = None, user: User = None) -> User:
    """Creates a User using the provided kwargs. The created user is saved to the
    database and returned.

    Args:
        **kwargs: Keyword arguments accepted by the User __init__

    Returns:
        User: The created User instance
    """

    if not user:
        user = db.query_unique(User, username=username, raise_missing=True)

    db.delete(user)

    # Sync child gardens
    initiate_user_sync()

    return user


def update_user(
    user: User = None,
    username: str = None,
    new_password: str = None,
    current_password: str = None,
    **kwargs,
) -> User:
    """Updates the provided User by setting its attributes to those provided by kwargs.
    The updated user object is then saved to the database and returned.

    Args:
        user: The User instance to be updated
        username: The username of the User instance to be updated
        new_password: The new password to be hashed
        current_password: The current password for verification and the new password
        **kwargs: Keyword arguments corresponding to User model attributes

    Returns:
        User: the updated User instance
    """
    if not user:
        user = db.query_unique(User, username=username, raise_missing=True)

    if not user.is_remote:
        # Only local accounts have passwords associated
        if new_password:
            if not current_password or verify_password(user, current_password):
                set_password(user, password=new_password)
            else:
                raise InvalidPasswordException("Current password incorrect")

    else:
        existing_user = db.query_unique(User, username=user.username)

        if existing_user and not existing_user.is_remote:
            # Update upstream roles, and alias user mappings
            if existing_user.upstream_roles != user.upstream_roles:
                # Roles changed, so cached tokens are no longer valid
                revoke_tokens(user=existing_user)
            existing_user.upstream_roles = user.upstream_roles
            existing_user.alias_user_mapping = user.alias_user_mapping

            user = existing_user

    for key, value in kwargs.items():
        if key == "roles":
            # Roles changed, so cached tokens are no longer valid
            revoke_tokens(user=user)
        setattr(user, key, value)

    user = db.update(user)
    # _publish_user_updated(user)

    # Sync child gardens
    initiate_user_sync()

    return user


def determine_max_permission(user: User) -> str:
    max_permission = "READ_ONLY"

    for roles in [user.local_roles, user.upstream_roles]:
        if roles:
            for role in roles:
                if role.permission == max_permission:
                    continue
                if role.permission == "GARDEN_ADMIN":
                    return role.permission

                if max_permission == "PLUGIN_ADMIN":
                    continue

                if role.permission == "PLUGIN_ADMIN":
                    max_permission = role.permission
                    continue

                if role.permission == "OPERATOR":
                    max_permission = role.permission

    return max_permission


def flatten_user_role(role: Role, flatten_roles: list):
    new_roles = []
    # loop through each scope to determine if we need to flatten further
    for scope_attribute in [
        "scope_gardens",
        "scope_namespaces",
        "scope_systems",
        "scope_instances",
        "scope_versions",
        "scope_commands",
    ]:
        if len(getattr(role, scope_attribute, [])) > 1:
            # Split scope and rerun

            for attribute_value in getattr(role, scope_attribute, []):
                new_role = deepcopy(role)
                setattr(new_role, scope_attribute, [attribute_value])
                new_roles.append(new_role)

            break

    # Role is as flat as it can be
    if len(new_roles) == 0:
        flatten_roles.append(role)

    # Keep Looping to flatten role
    for flatten_role in new_roles:
        flatten_user_role(flatten_role, flatten_roles)

    return flatten_roles


def generate_alias_user_mappings(
    user: User, target_garden: Garden, alias_user_mapping: list
):
    if target_garden.children:
        for child in target_garden.children:
            for alias_user_map in alias_user_mapping:
                if alias_user_map.target_garden == child.name:
                    user.alias_user_mapping.append(alias_user_map)
            generate_alias_user_mappings(user, child, alias_user_mapping)


def upstream_role_match(role: Role, target_garden: Garden):
    if upstream_role_match_garden(role, target_garden):
        return True

    if target_garden.children:
        for child in target_garden.children:
            if upstream_role_match(role, child):
                return True

    return False


def upstream_role_match_garden(role: Role, target_garden: Garden) -> bool:
    # If no scope attributes are populated, then it matches everything
    matchAll = True
    for scope_attribute in [
        "scope_gardens",
        "scope_namespaces",
        "scope_systems",
        "scope_instances",
        "scope_versions",
        "scope_commands",
    ]:
        if len(getattr(role, scope_attribute, [])) > 0:
            matchAll = False
            break

    if matchAll:
        return True

    if role.scope_gardens and len(role.scope_gardens) > 0:
        if target_garden.name not in role.scope_gardens:
            return False

    if target_garden.systems:
        for system in target_garden.systems:
            # Check for Command Role Filter
            if role.scope_commands and len(role.scope_commands) > 0:
                match = False
                for command in system.commands:
                    if command.name in role.scope_commands:
                        match = True
                        break

                if not match:
                    continue

            # Check for Instance Role Filter
            if role.scope_instances and len(role.scope_instances) > 0:
                match = False
                for instance in system.instances:
                    if instance.name in role.scope_instances:
                        match = True
                        break

                if not match:
                    continue

            # Check for Version Role Filter
            if role.scope_versions and len(role.scope_versions) > 0:
                match = False
                if system.version in role.scope_versions:
                    match = True
                if not match:
                    continue

            # Check for System Role Filter
            if role.scope_namespaces and len(role.scope_namespaces) > 0:
                match = False
                if system.name in role.scope_namespaces:
                    match = True

                if not match:
                    continue

            # Check for System Role Filter
            if role.scope_systems and len(role.scope_systems) > 0:
                match = False
                if system.name in role.scope_systems:
                    match = True
                if not match:
                    continue

            return True
    else:
        return True

    return False


def generate_downstream_user(target_garden: Garden, user: User) -> User:
    # Garden shares accounts, no filering applied
    if target_garden.shared_users:
        return User(
            username=user.username,
            is_remote=True,
            upstream_roles=user.local_roles,
            alias_user_mapping=user.alias_user_mapping,
        )

    downstream_user = None

    for alias_user_map in user.alias_user_mapping:
        if alias_user_map.target_garden == target_garden.name:
            downstream_user = User(username=alias_user_map.username, is_remote=True)

            generate_alias_user_mappings(
                downstream_user, target_garden, user.alias_user_mapping
            )

            for role in user.local_roles:
                for flatten_role in flatten_user_role(role, []):
                    if upstream_role_match(flatten_role, target_garden):
                        downstream_user.upstream_roles.append(flatten_role)

            for role in user.upstream_roles:
                for flatten_role in flatten_user_role(role, []):
                    if upstream_role_match(flatten_role, target_garden):
                        downstream_user.upstream_roles.append(flatten_role)

    return downstream_user


def initiate_garden_user_sync(garden_name: str = None, garden: Garden = None) -> None:
    """Syncs all users from this garden down to requested garden. Only the role
    assignments relevant to the garden will be included in the sync.

    Returns:
        None
    """
    from beer_garden.router import route

    if not garden:
        garden = get_garden(garden_name)

    garden_users = []
    for user in get_users():
        downstream_user = generate_downstream_user(garden, user)
        if downstream_user:
            garden_users.append(downstream_user)

    operation = Operation(
        operation_type="USER_UPSTREAM_SYNC",
        target_garden_name=garden.name,
        kwargs={
            "upstream_users": SchemaParser.serialize_user(
                garden_users, to_string=False, many=True
            ),
        },
    )

    route(operation)


def initiate_user_sync() -> None:
    """Syncs all users from this garden down to all gardens. Only the role
    assignments relevant to each garden will be included in the sync.

    Returns:
        None
    """
    from beer_garden.router import route

    for child in get_gardens(include_local=False):
        child_users = []
        for user in get_users():
            downstream_user = generate_downstream_user(child, user)
            if downstream_user:
                child_users.append(downstream_user)

        operation = Operation(
            operation_type="USER_UPSTREAM_SYNC",
            target_garden_name=child.name,
            kwargs={
                "upstream_users": SchemaParser.serialize_user(
                    child_users, to_string=False, many=True
                ),
            },
        )

        route(operation)


def upstream_user_sync(upstream_user: User) -> User:
    local_user = db.query_unique(User, username=upstream_user.username)

    if local_user is None:
        return db.create(upstream_user)

    if local_user.is_remote:
        return db.update(upstream_user)

    local_user.alias_user_mapping = upstream_user.alias_user_mapping
    local_user.upstream_roles = upstream_user.upstream_roles
    return db.update(local_user)


def upstream_users_sync(upstream_users=[]):
    upstream_users_brewtils = SchemaParser.parse_user(
        upstream_users, many=True, from_string=False
    )
    local_users = get_users()

    # Add/Update Upstream Users
    for upstream_user in upstream_users:
        new_user = True
        for user in local_users:
            if upstream_user.username != user.username:
                continue
            new_user = False
            user.alias_user_mapping = upstream_user.alias_user_mapping
            user.upstream_roles = upstream_user.upstream_roles
            db.update(user)
        if new_user:
            upstream_user = db.create(upstream_user)

    # Purge Remote Users not provided
    for user in local_users:
        if user.is_remote:
            user_found = False
            for upstream_user in upstream_users_brewtils:
                if upstream_user.username == user.username:
                    user_found = True
                    continue
            if user_found:
                continue
            db.delete(user)

    # Sync child gardens
    initiate_user_sync()


def ensure_users():
    """Create user accounts if necessary"""
    _create_admin()
    _create_plugin_user()
    rescan()


def _create_admin():
    """Create the default admin user if necessary"""
    username = config.get("auth.default_admin.username")
    password = config.get("auth.default_admin.password")
    try:
        admin = get_user(username=username)
        set_password(admin, password)
        db.update(admin)
    except DoesNotExist:
        logger.info("Creating default admin user with username: %s", username)
        admin = User(
            username=username, roles=["superuser"], protected=True, file_generated=True
        )
        set_password(admin, password)
        db.create(admin)


def _create_plugin_user():
    """Create the default user to run Plugins if necessary"""
    username = config.get("plugin.local.auth.username")
    password = config.get("plugin.local.auth.password")
    try:
        plugin_user = get_user(username=username)
        set_password(plugin_user, password)
        db.update(plugin_user)
    except DoesNotExist:
        # Sanity check to make sure we don't accidentally create two
        # users with the same name
        logger.info("Creating default plugin user with username: %s", username)
        plugin_user = User(
            username=username, roles=["plugin"], protected=True, file_generated=True
        )
        set_password(plugin_user, password)
        db.create(plugin_user)


def remove_local_role_assignments_for_role(role: Role) -> int:
    """Remove all User role assignments for the provided Role.

    Args:
        role: The Role document object

    Returns:
        int: The number of users role was removed from
    """
    # Avoid circular import

    impacted_users = db.query(User, filter_params={"roles__match": role.name})

    for user in impacted_users:
        user.roles.remove(role.name)
        update_user(user=user)
        # Roles changed, so cached tokens are no longer valid
        revoke_tokens(user=user)

    return len(impacted_users)


def update_local_role_assignments_for_role(role: Role) -> int:
    """Update all User role assignments for the provided Role.

    Args:
        role: The Role document object

    Returns:
        int: The number of users role was removed from
    """
    # Avoid circular import

    impacted_users = db.query(User, filter_params={"roles__match": role.name})

    for user in impacted_users:
        # Roles changed, so cached tokens are no longer valid
        revoke_tokens(user=user)

    return len(impacted_users)


def handle_event(event: Event) -> None:
    # Only handle events from downstream gardens
    if event.garden == config.get("garden.name"):
        if event.name == "ROLE_DELETED":
            remove_local_role_assignments_for_role(event.payload)
        elif event.name == "USER_UPDATED":
            initiate_user_sync()


def _publish_user_updated(user):
    """Publish an event with the updated user information"""

    # We use publish rather than publish_event here so that we can hijack the metadata
    # field to store our actual data. This is done to avoid needing to deal in brewtils
    # models, which the publish_event decorator requires us to do.
    publish(
        Event(
            name=Events.USER_UPDATED.name,
            metadata={
                "garden": config.get("garden.name"),
                "user": user,
            },
        )
    )
