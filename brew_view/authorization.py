import base64
import functools
from datetime import datetime, timedelta
from enum import Enum

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import brew_view
from bg_utils.models import Principal
from brewtils.models import (
    Principal as BrewtilsPrincipal,
    Role as BrewtilsRole
)


class Permissions(Enum):
    ALL = 'all'
    COMMAND_ALL = 'command_all'
    COMMAND_CREATE = 'command_create'
    COMMAND_READ = 'command_read'
    COMMAND_UPDATE = 'command_update'
    COMMAND_DELETE = 'command_delete'
    REQUEST_ALL = 'request_all'
    REQUEST_CREATE = 'request_create'
    REQUEST_READ = 'request_read'
    REQUEST_UPDATE = 'request_update'
    REQUEST_DELETE = 'request_delete'
    SYSTEM_ALL = 'system_all'
    SYSTEM_CREATE = 'system_create'
    SYSTEM_READ = 'system_read'
    SYSTEM_UPDATE = 'system_update'
    SYSTEM_DELETE = 'system_delete'
    INSTANCE_ALL = 'instance_all'
    INSTANCE_CREATE = 'instance_create'
    INSTANCE_READ = 'instance_read'
    INSTANCE_UPDATE = 'instance_update'
    INSTANCE_DELETE = 'instance_delete'
    QUEUE_ALL = 'queue_all'
    QUEUE_CREATE = 'queue_create'
    QUEUE_READ = 'queue_read'
    QUEUE_UPDATE = 'queue_update'
    QUEUE_DELETE = 'queue_delete'
    USER_ALL = 'user_all'
    USER_CREATE = 'user_create'
    USER_READ = 'user_read'
    USER_UPDATE = 'user_update'
    USER_DELETE = 'user_delete'


def authenticated(method=None, permissions=None):
    """Decorate methods with this to require various permissions"""

    if method is None:
        return functools.partial(authenticated, permissions=permissions)

    # Convert to strings for easier comparison
    permission_strings = set(p.name for p in permissions)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not has_permission(self.current_user, permission_strings):
            raise HTTPError(403)

        return method(self, *args, **kwargs)

    return wrapper


def has_permission(principal, required_permissions):
    """Determine if a principal has access to a resource

    :param principal: the principal to test
    :param required_permissions: set of strings
    :return: bool yes or no
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
