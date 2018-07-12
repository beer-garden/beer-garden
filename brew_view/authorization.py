import base64
import functools
from enum import Enum

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context

import brew_view
from bg_utils.models import Principal
from brewtils.errors import AuthorizationRequired, RequestForbidden
from brewtils.models import (
    Principal as BrewtilsPrincipal,
    Role as BrewtilsRole
)


class Permissions(Enum):
    ALL = 'bg-all'
    COMMAND_CREATE = 'bg-command-create'
    COMMAND_READ = 'bg-command-read'
    COMMAND_UPDATE = 'bg-command-update'
    COMMAND_DELETE = 'bg-command-delete'
    REQUEST_CREATE = 'bg-request-create'
    REQUEST_READ = 'bg-request-read'
    REQUEST_UPDATE = 'bg-request-update'
    REQUEST_DELETE = 'bg-request-delete'
    SYSTEM_CREATE = 'bg-system-create'
    SYSTEM_READ = 'bg-system-read'
    SYSTEM_UPDATE = 'bg-system-update'
    SYSTEM_DELETE = 'bg-system-delete'
    INSTANCE_CREATE = 'bg-instance-create'
    INSTANCE_READ = 'bg-instance-read'
    INSTANCE_UPDATE = 'bg-instance-update'
    INSTANCE_DELETE = 'bg-instance-delete'
    QUEUE_CREATE = 'bg-queue-create'
    QUEUE_READ = 'bg-queue-read'
    QUEUE_UPDATE = 'bg-queue-update'
    QUEUE_DELETE = 'bg-queue-delete'
    USER_CREATE = 'bg-user-create'
    USER_READ = 'bg-user-read'
    USER_UPDATE = 'bg-user-update'
    USER_DELETE = 'bg-user-delete'


Permissions.values = {p.value for p in Permissions}


def authenticated(method=None, permissions=None):
    """Decorate methods with this to require various permissions"""

    if method is None:
        return functools.partial(authenticated, permissions=permissions)

    # Convert to strings for easier comparison
    permission_strings = set(p.value for p in permissions)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not has_permission(self.current_user, permission_strings):
            # Need to make a distinction between "you need to be authenticated
            # to do this" and "you've been authenticated and denied"
            if self.current_user == brew_view.anonymous_principal:
                raise AuthorizationRequired()
            else:
                raise RequestForbidden('Action requires permission %s' %
                                       permissions[0].value)

        return method(self, *args, **kwargs)

    return wrapper


def has_permission(principal, required_permissions):
    """Determine if a principal has access to a resource

    Args:
        principal: the principal to test
        required_permissions: set of strings

    Returns:
        bool yes or no
    """
    if Permissions.ALL.value in principal.permissions:
        return True

    return bool(required_permissions.intersection(principal.permissions))


def coalesce_permissions(role_list):
    """Determine permissions"""

    if not role_list:
        return set(), set()

    aggregate_roles = set()
    aggregate_perms = set()

    for role in role_list:
        aggregate_roles.add(role.name)
        aggregate_perms |= set(role.permissions)

        nested_roles, nested_perms = coalesce_permissions(role.roles)
        aggregate_roles |= nested_roles
        aggregate_perms |= nested_perms

    return aggregate_roles, aggregate_perms


def basic_auth(auth_header):
    """Determine if a basic authorization header is valid

    Args:
        auth_header: The Authorization header. Should start with 'Basic '.

    Returns:
        Brewtils principal if auth_header is valid, None otherwise
    """
    auth_decoded = base64.b64decode(auth_header[6:]).decode()
    username, password = auth_decoded.split(':')

    try:
        principal = Principal.objects.get(username=username)

        if custom_app_context.verify(password, principal.hash):
            return principal
    except DoesNotExist:
        # Don't handle this differently to prevent an attacker from being able
        #  to enumerate a list of user names
        pass

    return None


def bearer_auth(auth_header):
    """Determine if a bearer authorization header is valid

    Args:
        auth_header: The Authorization header. Should start with 'Bearer '.

    Returns:
        Brewtils principal if auth_header is valid, None otherwise
    """
    token = auth_header.split(' ')[1]

    decoded = jwt.decode(token,
                         key=brew_view.config.auth.token.secret,
                         algorithm=brew_view.config.auth.token.algorithm)

    return BrewtilsPrincipal(
        id=decoded['sub'],
        username=decoded.get('username', ''),
        roles=[BrewtilsRole(name=role) for role in decoded.get('roles', [])],
        permissions=decoded.get('permissions', [])
    )
