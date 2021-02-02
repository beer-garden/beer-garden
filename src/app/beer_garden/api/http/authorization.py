# -*- coding: utf-8 -*-
import base64
from enum import Enum

import jwt
import wrapt
from brewtils.errors import RequestForbidden
from brewtils.models import Principal as BrewtilsPrincipal, Role as BrewtilsRole
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import beer_garden.api.http
import beer_garden.config as config
from beer_garden.db.mongo.models import Principal, Role


class Permissions(Enum):
    """Admin permissions are required to execute anything within the Admin drop-down in
    regards to Systems and Gardens. Local Admins can manage user roles  and permissions.
    """

    # All of the permissions
    ALL = "bg-all"
    # Permission to create non Admin data
    CREATE = "bg-create"
    # Permission to retrieve non Admin data
    READ = "bg-read"
    # Permission to update non Admin data
    UPDATE = "bg-update"
    # Permission to Delete non Admin data
    DELETE = "bg-delete"
    # Admin actions outside of User Management
    SYSTEM_ADMIN = "bg-system-admin"
    # Permission to manage local users
    LOCAL_ADMIN = "bg-local-admin"


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

        return wrapped(*args, **kwargs)

    return wrapper


def check_permission(principal, required_permissions):
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
    if Permissions.ALL.value in principal.permissions:
        return True

    # Convert to strings for easier comparison
    permission_strings = set(p.value for p in required_permissions)

    if not permission_strings.intersection(principal.permissions):
        # Need to make a distinction between "you need to be authenticated
        # to do this" and "you've been authenticated and denied"
        if principal == beer_garden.api.http.anonymous_principal:
            raise HTTPError(status_code=401)
        else:
            raise RequestForbidden(
                "Action requires permissions %s" % permission_strings
            )


def anonymous_principal() -> BrewtilsPrincipal:
    """Load correct anonymous permissions

    This exists in a weird space. We need to set the roles attribute to a 'real'
    Role object so it works correctly when the REST handler goes to serialize
    this principal.

    However, we also need to set the permissions attribute to the consolidated
    permission list so that ``check_permission`` will be able to do a comparison
    without having to calculate effective permissions every time.
    """

    # auth_config = config.get("auth")
    # if auth_config.enabled and auth_config.guest_login_enabled:
    #     roles = Principal.objects.get(username="anonymous").roles
    # elif auth_config.enabled:
    #     # By default, if no guest login is available, there is no anonymous
    #     # user, which means there are no roles.
    #     roles = []
    # else:
    roles = [Role(name="bg-admin", permissions=["bg-all"])]

    _, permissions = coalesce_permissions(roles)

    return BrewtilsPrincipal(username="anonymous", roles=roles, permissions=permissions)


def coalesce_permissions(role_list):
    """Determine permissions"""

    if not role_list:
        return set(), set()

    aggregate_roles = set()
    aggregate_perms = set()

    for role in role_list:
        aggregate_roles.add(role.name)
        aggregate_perms |= set(role.permissions)

    return aggregate_roles, aggregate_perms


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


def proxy_auth(request):
    """Determine a principle from custom proxy Authorization headers. Only enable if you
    control the proxy and can ensure the fields are populated properly.
    Args:
        request: The request to authenticate
    Returns:
        Brewtils principal if proxy headers are valid, None otherwise
    """

    auth_config = config.get("auth")

    if not auth_config.proxy.enabled:
        return None

    # If the secret set does not match what was provided, then do not accept. This could
    # have been sent from a non-proxied source.
    if (
        auth_config.proxy_secret_header is not None
        and auth_config.proxy_secret
        != request.headers.get(auth_config.proxy_secret_header, None)
    ):
        return None

    username = None
    roles = None

    # Username is exepected to a string object
    if auth_config.proxy_username_header:
        username = request.headers.get(auth_config.proxy_username_header, None)

    # roles is expected to be in a list format (i.e. roles = "role1,role2,role3")
    if auth_config.proxy_roles_header:
        raw_roles = request.headers.get(auth_config.proxy_roles_header, None)

        if raw_roles:
            roles = raw_roles.split(",").strip()

    # No headers were set that can be processed
    if username is None and roles is None:
        return None

    # If the user name exists in the database, return that, else generate a new Principal Object
    try:
        if username:
            principal = Principal.objects.get(username=username)
        else:
            # Roles were forwarded without a username
            principal = BrewtilsPrincipal(username="PROXY-USER")
    except DoesNotExist:
        principal = BrewtilsPrincipal(username=username)

    for role in roles:
        try:
            # If the role is already mapped, skip
            for principal_role in principal.roles:
                if principal_role.name == role:
                    continue

            # If the role maps to a known role, append
            principal.roles.append(Role.objects.get(name=role))
        except DoesNotExist:
            # We won't add roles that don't exist in the database
            pass

    # No valid user was generated through the headers
    if username is None and len(principal.roles) == 0:
        return None

    _, permissions = coalesce_permissions(principal.roles)
    principal.permissions = permissions

    return principal


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
        permissions=decoded.get("permissions", []),
    )


class AuthMixin(object):
    auth_providers: frozenset = [proxy_auth, bearer_auth, basic_auth]

    def get_current_user(self):
        """Use registered handlers to determine current user"""

        for provider in self.auth_providers:
            principal = provider(self.request)

            if principal is not None:
                return principal

        return beer_garden.api.http.anonymous_principal
