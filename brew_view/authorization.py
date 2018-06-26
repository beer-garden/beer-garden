import base64
import functools
from datetime import datetime, timedelta

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


def authenticated(method=None, permissions=None):
    """Decorate methods with this to require various permissions"""

    if method is None:
        return functools.partial(authenticated, permissions=permissions)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # If no user don't even bother
        if not self.current_user:
            raise HTTPError(403)

        # User permissions must contain ALL specified permissions
        if not has_permission(self.current_user, permissions):
            raise HTTPError(403)

        return method(self, *args, **kwargs)

    return wrapper


def has_permission(principal, required_permissions):
    if 'all' in principal.permissions:
        return True

    return set(required_permissions).issubset(principal.permissions)


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
