# -*- coding: utf-8 -*-
import base64
from enum import Enum

import jwt
import wrapt

from beer_garden.users import coalesce_permissions
from brewtils.errors import RequestForbidden
from brewtils.models import (
    Principal as BrewtilsPrincipal,
    Role as BrewtilsRole,
    Permission as BrewtilsPermission,
)
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import beer_garden.api.http
import beer_garden.config as config
from beer_garden.db.mongo.models import Principal
from brewtils.schema_parser import SchemaParser


class Permissions(Enum):
    """Admin permissions are required to execute anything within the Admin drop-down in
    regards to Systems and Gardens. Local Admins can manage user roles  and permissions.
    """
    READ = 1
    CREATE = 2
    MAINTAINER = 3
    ADMIN = 4


PermissionRequiredAccess = {
    Permissions.READ: ["ADMIN", "MAINTAINER", "CREATE", "READ"],
    Permissions.CREATE: ["ADMIN", "MAINTAINER", "CREATE"],
    Permissions.MAINTAINER: ["ADMIN", "MAINTAINER"],
    Permissions.ADMIN: ["ADMIN"],
}

Permissions.values = {p.value for p in Permissions}


def authenticated(permissions=None):
    """Decorator used to require permissions for access to a resource.

    Args:
        permissions: Collection of Permissions enums. Note that if multiple
            permissions are specified then a principal must have all of them
            to access the resource.

    Returns:
        The wrapper function
    """

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        # The interplay between wrapt and gen.coroutine causes things to get
        # a little confused, so we have to be flexible
        handler = instance or args[0]

        check_permission(handler.current_user, permissions)
        handler.required_permissions = permissions
        return wrapped(*args, **kwargs)

    return wrapper


def check_permission(principal, required_permissions, is_local=False):
    """Determine if a principal has access to a resource

    Args:
        principal: the principal to test
        required_permissions: collection of strings

    Returns:
        None

    Raises:
        HTTPError(status_code=401): The requested resource requires auth
        RequestForbidden(status_code=403): The current principal does not have
            permission to access the requested resource
    """

    # Grab the accesses that grand access for Permission
    permission_strings = set()
    for required in required_permissions:
        permission_strings |= set(PermissionRequiredAccess[required])

    # If no permissions required, grant access
    if len(permission_strings) == 0:
        return

    # If user has access to that permission, grant access
    for permission in principal.permissions:
        if permission.access in permission_strings:
            if is_local:
                if permission.is_local:
                    return
            else:
                return

    # Determine correct error code to throw
    if principal == beer_garden.api.http.anonymous_principal:
        raise HTTPError(status_code=401)
    else:
        if is_local:
            raise RequestForbidden("Action requires local permissions %s" % permission_strings)
        else:
            raise RequestForbidden("Action requires permissions %s" % permission_strings)


def anonymous_principal() -> BrewtilsPrincipal:
    """Load correct anonymous permissions

    This exists in a weird space. We need to set the roles attribute to a 'real'
    Role object so it works correctly when the REST handler goes to serialize
    this principal.

    However, we also need to set the permissions attribute to the consolidated
    permission list so that ``check_permission`` will be able to do a comparison
    without having to calculate effective permissions every time.
    """

    auth_config = config.get("auth")
    if auth_config.enabled and auth_config.guest_login_enabled:
        roles = Principal.objects.get(username="anonymous").roles
    elif auth_config.enabled:
        # By default, if no guest login is available, there is no anonymous
        # user, which means there are no roles.
        roles = []
    else:
        roles = [
            BrewtilsRole(
                name="bg-admin",
                permissions=[BrewtilsPermission(is_local=True, access="ADMIN")],
            )
        ]

    _, permissions = coalesce_permissions(roles)

    return BrewtilsPrincipal(username="anonymous", roles=roles, permissions=permissions)


def basic_auth(request):
    """Determine if a basic authorization header is valid

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if auth_header is valid, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return None

    auth_decoded = base64.b64decode(auth_header[6:]).decode()
    username, password = auth_decoded.split(":")

    try:
        principal = Principal.objects.get(username=username)

        if custom_app_context.verify(password, principal.hash):
            return principal
    except DoesNotExist:
        # Don't handle this differently to prevent an attacker from being able
        #  to enumerate a list of user names
        pass

    return None


def bearer_auth(request):
    """Determine a principal from a JWT in the Authorization header

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    return _principal_from_token(token)


def query_token_auth(request):
    """Determine a principal from a JWT in query parameter 'token'

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    token_args = request.query_arguments.get("token", None)
    if token_args is None:
        return None

    return _principal_from_token(token_args[0])


def _principal_from_token(token):
    """Determine a principal from a JWT

    Args:
        token: The JWT

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    auth_config = config.get("auth")
    try:
        decoded = jwt.decode(
            token, key=auth_config.token.secret, algorithm=auth_config.token.algorithm
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPError(status_code=401, log_message="Signature expired")

    return BrewtilsPrincipal(
        id=decoded["sub"],
        username=decoded.get("username", ""),
        roles=[BrewtilsRole(name=role) for role in decoded.get("roles", [])],
        permissions=[SchemaParser.parse_permission(permission, from_string=True) for permission in decoded.get("permissions", [])],
    )


class AuthMixin(object):
    auth_providers: frozenset = None

    def get_current_user(self):
        """Use registered handlers to determine current user"""

        for provider in self.auth_providers:
            principal = provider(self.request)

            if principal is not None:
                return principal

        return beer_garden.api.http.anonymous_principal
