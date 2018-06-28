import base64
import functools
from datetime import datetime, timedelta
from enum import Enum

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import brew_view
from bg_utils.models import Principal, Role
from brewtils.models import (
    Principal as BrewtilsPrincipal,
    Role as BrewtilsRole
)


class Permissions(Enum):
    ALL = 'bg-all'
    COMMAND_ALL = 'bg-command-all'
    COMMAND_CREATE = 'bg-command-create'
    COMMAND_READ = 'bg-command-read'
    COMMAND_UPDATE = 'bg-command-update'
    COMMAND_DELETE = 'bg-command-delete'
    REQUEST_ALL = 'bg-request-all'
    REQUEST_CREATE = 'bg-request-create'
    REQUEST_READ = 'bg-request-read'
    REQUEST_UPDATE = 'bg-request-update'
    REQUEST_DELETE = 'bg-request-delete'
    SYSTEM_ALL = 'bg-system-all'
    SYSTEM_CREATE = 'bg-system-create'
    SYSTEM_READ = 'bg-system-read'
    SYSTEM_UPDATE = 'bg-system-update'
    SYSTEM_DELETE = 'bg-system-delete'
    INSTANCE_ALL = 'bg-instance-all'
    INSTANCE_CREATE = 'bg-instance-create'
    INSTANCE_READ = 'bg-instance-read'
    INSTANCE_UPDATE = 'bg-instance-update'
    INSTANCE_DELETE = 'bg-instance-delete'
    QUEUE_ALL = 'bg-queue-all'
    QUEUE_CREATE = 'bg-queue-create'
    QUEUE_READ = 'bg-queue-read'
    QUEUE_UPDATE = 'bg-queue-update'
    QUEUE_DELETE = 'bg-queue-delete'
    USER_ALL = 'bg-user-all'
    USER_CREATE = 'bg-user-create'
    USER_READ = 'bg-user-read'
    USER_UPDATE = 'bg-user-update'
    USER_DELETE = 'bg-user-delete'


def authenticated(method=None, permissions=None):
    """Decorate methods with this to require various permissions"""

    if method is None:
        return functools.partial(authenticated, permissions=permissions)

    # Convert to strings for easier comparison
    permission_strings = set(p.value for p in permissions)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not has_permission(self.current_user, permission_strings):
            raise HTTPError(403)

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
    if not principal:
        return False

    if Permissions.ALL.value in principal.permissions:
        return True

    return bool(required_permissions.intersection(principal.permissions))


def generate_token(principal):
    current_time = datetime.utcnow()

    # Permissions are a union of all role's permissions and specific permissions
    role_names = []
    permissions = set()
    for role in principal.roles:
        role_names.append(role.name)
        permissions |= set(role.permissions)
    permissions |= set(principal.permissions)

    payload = {
        'sub': str(principal.id),
        'iat': current_time,
        'exp': current_time + timedelta(minutes=20),
        'username': principal.username,
        'roles': role_names,
        'permissions': list(permissions),
    }
    return jwt.encode(payload,
                      brew_view.tornado_app.settings["cookie_secret"],
                      algorithm='HS256')


def anonymous_user():
    try:
        # TODO - These won't change, so we should just load them on startup
        anonymous_permissions = Role.objects.get(name='bg-anonymous').permissions
    except DoesNotExist:
        anonymous_permissions = []

    return BrewtilsPrincipal(permissions=anonymous_permissions)


def basic_auth(auth_header):
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
    token = auth_header.split(' ')[1]

    decoded = jwt.decode(token,
                         brew_view.tornado_app.settings["cookie_secret"],
                         algorithm='HS256')

    return BrewtilsPrincipal(
        id=decoded['sub'],
        username=decoded.get('username', ''),
        roles=[BrewtilsRole(name=role) for role in decoded.get('roles', [])],
        permissions=decoded.get('permissions', [])
    )
