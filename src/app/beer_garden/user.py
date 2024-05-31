import logging
import yaml

from brewtils.models import Event, Events, Operation, User, Garden, Role, UserToken
from copy import deepcopy

from beer_garden import config
import beer_garden.db.api as db
from beer_garden.events import publish
# from beer_garden.role import RoleSyncSchema, role_sync_status, sync_roles
from beer_garden.errors import InvalidPasswordException
from beer_garden.garden import get_gardens, get_garden
from beer_garden.role import get_role
from mongoengine import DoesNotExist

from passlib.apps import custom_app_context


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
    """
    """
    return db.create(token)

def get_token(uuid: str):
    """
    """
    return db.query_unique(UserToken, uuid=uuid, raise_missing=True)

def delete_token(token: UserToken):
    """
    """
    return db.delete(token)

def has_token(username: str):
    return db.count(UserToken, username=username) > 0

def revoke_tokens(user: User = None, username: str = None) -> None:
    """Remove all tokens from the user's list of valid tokens. This is useful for
    requiring the user to explicitly login, which one may want to do for a variety
    of reasons.
    """
    for user_token in db.query(UserToken, username=user.username if user else username):
        db.delete(user_token)

def get_user(username: str = None, id: str = None, include_roles: bool = True) -> User:
    """
    """
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
    with open(config.get("auth.user_definition_file"), "r") as config_file:
        return yaml.safe_load(config_file)

def rescan():
    """Recan the users config"""
    users_config = load_users_config()
    for user in users_config:
        kwargs = {"username": user.get("username"), "roles": user.get("roles")}
        user = User(**kwargs)
        try:
            existing = get_user(user.username)
            if existing:
                update_user(existing,
                            **kwargs)
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

    return user



def update_user(user: User = None, username: str = None, new_password: str = None, current_password: str = None, **kwargs) -> User:
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
            # Update remote roles, and remote user mappings
            if existing_user.remote_roles != user.remote_roles:
                # Roles changed, so cached tokens are no longer valid
                revoke_tokens(user = existing_user)
            existing_user.remote_roles = user.remote_roles
            existing_user.remote_user_mapping = user.remote_user_mapping

            user = existing_user
    
    for key, value in kwargs.items():
        if key == "roles":
            # Roles changed, so cached tokens are no longer valid
            revoke_tokens(user = user)
        setattr(user, key, value)

    user = db.update(user)
    _publish_user_updated(user)

    return user


def flatten_user_role(role: Role, flatten_roles: list):
    new_roles = []
    #loop through each scope to determine if we need to flatten further
    for scope_attribute in ["scope_gardens","scope_namespaces", "scope_systems", "scope_instances", "scope_versions","scope_commands"]:
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

def generate_remote_user_mappings(user: User, target_garden: Garden, remote_user_mapping: list):
    if target_garden.children:
        for child in target_garden.children:
            for remote_user_map in remote_user_mapping:
                if remote_user_map.target_garden == child.name:
                    user.remote_user_mapping.append(remote_user_map)
            generate_remote_user_mappings(user, child, remote_user_mapping)
    

def remote_role_match(role: Role, target_garden: Garden):
    if remote_role_match_garden(role, target_garden):
        return True
    
    if target_garden.children:
        for child in target_garden.children:
            if remote_role_match(role, child):
                return True
    
    return False

def remote_role_match_garden(role: Role, target_garden: Garden) -> bool:

    # If no scope attributes are populated, then it matches everything
    matchAll = True
    for scope_attribute in ["scope_gardens","scope_namespaces", "scope_systems", "scope_instances", "scope_versions","scope_commands"]:
        if len(getattr(role, scope_attribute, [])) > 0:
            matchAll = False
            break

    if matchAll:
        return True

    if role.scope_gardens and len(role.scope_gardens) > 0:
        if target_garden.name not in role.scope_gardens:
            return False
        
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

    return False

def generate_remote_user(target_garden: Garden, user: User) -> User:

    # Garden shares accounts, no filering applied
    if target_garden.shared_users:
        return User(username=user.username, is_remote=True, remote_roles=user.local_roles, remote_user_mapping=user.remote_user_mapping)

    remote_user = None

    for remote_user_map in user.remote_user_mapping:
        if remote_user_map.target_garden == target_garden.name:
            remote_user = User(username=remote_user_map.username, is_remote=True)

            generate_remote_user_mappings(remote_user, target_garden, user.remote_user_mapping)

            for role in user.local_roles:
                for flatten_role in flatten_user_role(role, []):
                    if remote_role_match(flatten_role, target_garden):
                        remote_user.remote_roles.append(flatten_role)

            for role in user.remote_roles:
                for flatten_role in flatten_user_role(role, []):
                    if remote_role_match(flatten_role, target_garden):
                        remote_user.remote_roles.append(flatten_role)
    
    return remote_user

def initiate_garden_user_sync(garden_name: str = None, garden: Garden = None) -> None:
    """Syncs all users from this garden down to requested garden. Only the role
    assignments relevant to the garden will be included in the sync.

    Returns:
        None
    """
    from beer_garden.router import route

    if not garden:
        garden = get_garden(garden_name)
    
    garden_remote_users = []
    for user in get_users():
        remote_user = generate_remote_user(garden, user)
        if remote_user:
            garden_remote_users.append(remote_user)
    
    operation = Operation(
        operation_type="USER_REMOTE_SYNC",
        target_garden_name=garden.name,
        kwargs={
            "remote_users": garden_remote_users,
        },
    )

    route(operation)  
        
def initiate_user_sync() -> None:
    """Syncs all users from this garden down to all remote gardens. Only the role
    assignments relevant to each remote garden will be included in the sync.

    Returns:
        None
    """
    from beer_garden.router import route
    
    for child in get_gardens(include_local=False):
        child_remote_users = []
        for user in get_users():
            remote_user = generate_remote_user(child, user)
            if remote_user:
                child_remote_users.append(remote_user)
        
        operation = Operation(
            operation_type="USER_REMOTE_SYNC",
            target_garden_name=child.name,
            kwargs={
                "remote_users": child_remote_users,
            },
        )

        route(operation)

def remote_user_sync(remote_user: User) -> User:
    local_user = db.query_unique(User, username=remote_user.username)

    if local_user is None:
        return db.create(remote_user)
    
    if local_user.is_remote:
        return db.update(remote_user)
    
    local_user.remote_user_mapping = remote_user.remote_user_mapping
    local_user.remote_roles = remote_user.remote_roles
    return db.update(local_user)

def remote_users_sync(remote_users: list[User] = []):

    for user in get_users():
        remote_user = next((remote_user for remote_user in remote_users if remote_user.username == user.username), None)

        if user.is_remote:                    
            if remote_user is None:
                # If remote and not in the provided list, then the user was deleted upstream
                db.delete(user)
            else:
                db.update(remote_user)
        else:
            if remote_user:
                # Update only the remote fields
                user.remote_user_mapping = remote_user.remote_user_mapping
                user.remote_roles = remote_user.remote_roles

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
        admin = User(username=username, roles=["superuser"])
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
        plugin_user = User(username=username, roles=["plugin"])
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
    
    impacted_users = db.query(
            User, filter_params={"roles__match": role.name}
        )

    for user in impacted_users:
        user.roles.remove(role.name)
        update_user(user=user)
        # Roles changed, so cached tokens are no longer valid
        revoke_tokens(user = user)

    return len(impacted_users)

#Old Stuff
################################

# def initiate_user_sync() -> None:
#     """Syncs all users from this garden down to all remote gardens. Only the role
#     assignments relevant to each remote garden will be included in the sync.

#     Returns:
#         None
#     """
#     # Avoiding circular imports
#     from beer_garden.api.http.schemas.v1.user import UserSyncSchema
#     from beer_garden.router import route

#     users = User.objects.all()
#     gardens = Garden.objects.filter(
#         connection_type__nin=["LOCAL", None], status="RUNNING"
#     )

#     for garden in gardens:
#         filtered_users = [
#             _filter_role_assigments_by_garden(user, garden) for user in users
#         ]
#         serialized_users = (
#             UserSyncSchema(many=True, strict=True).dump(filtered_users).data
#         )

#         roles = Role.objects.all()
#         serialized_roles = RoleSyncSchema(many=True).dump(roles).data

#         operation = Operation(
#             operation_type="USER_SYNC",
#             target_garden_name=garden.name,
#             kwargs={
#                 "serialized_roles": serialized_roles,
#                 "serialized_users": serialized_users,
#             },
#         )

#         route(operation)


# def user_sync(serialized_roles: List[dict], serialized_users: List[dict]) -> None:
#     """Function called for the USER_SYNC operation type. This imports the supplied list
#     of serialized_users and then initiates a USER_SYNC on any remote gardens. The
#     serialized_users dicts are expected to have been generated via UserSyncSchema.
#     NOTE: Existing users (matched by username) will be updated if present in the
#     serialized_users list.

#     Args:
#         serialized_users: Serialized list of users

#     Returns:
#         None
#     """
#     sync_roles(serialized_roles)
#     _import_users(serialized_users)
#     _publish_users_imported()
#     initiate_user_sync()



def handle_event(event: Event) -> None:
    # Only handle events from downstream gardens
    if event.garden == config.get("garden.name"):
        if event.name == "ROLE_DELETE":
            remove_local_role_assignments_for_role(event.payload)


    # if event.name == "USER_UPDATED":
    #     _handle_user_updated_event(event)


# def _import_users(serialized_users: List[dict]) -> None:
#     """Imports users from a list of dictionaries."""
#     # Avoiding circular import. Schemas should probably be moved outside of the http
#     # heirarchy.
#     from beer_garden.api.http.schemas.v1.user import UserPatchSchema

#     for serialized_user in serialized_users:
#         username = serialized_user["username"]

#         try:
#             updated_user_data = UserPatchSchema(strict=True).load(serialized_user).data

#             try:
#                 user = User.objects.get(username=username)
#             except User.DoesNotExist:
#                 if len(updated_user_data["role_assignments"]) > 0:
#                     user = User(username=username)
#                     user.save()
#                 else:
#                     continue

#             update_user(user, **updated_user_data)

#         except ValidationError as exc:
#             logger.info(f"Failed to import user {username} due to error: {exc}")


# def _handle_user_updated_event(event):
#     """Handling for USER_UPDATED events"""
#     # NOTE: This event stores its data in the metadata field as a workaround to the
#     # brewtils models dependency inherent in the more typical event publishing flow
#     try:
#         garden = event.metadata["garden"]
#         updated_user = event.metadata["user"]
#         updated_at = event.timestamp

#         username = updated_user["username"]
#         role_assignments = updated_user["role_assignments"]

#         try:
#             remote_user = RemoteUser.objects.get(garden=garden, username=username)
#         except RemoteUser.DoesNotExist:
#             remote_user = RemoteUser(garden=garden, username=username)

#         remote_user.role_assignments = role_assignments
#         remote_user.updated_at = updated_at
#         remote_user.save()
#     except KeyError:
#         logger.error("Error parsing %s event from garden %s", event.name, event.garden)





# def _publish_users_imported():
#     """Publish an event indicating that a user sync was completed"""
#     publish(
#         Event(
#             name=Events.USERS_IMPORTED.name,
#             metadata={
#                 "garden": config.get("garden.name"),
#             },
#         )
#     )


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
