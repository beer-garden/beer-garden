import base64
from enum import Enum

import jwt
import wrapt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import brew_view
from bg_utils.models import Principal, Role
from brewtils.errors import RequestForbidden
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
    EVENT_CREATE = 'bg-event-create'
    EVENT_READ = 'bg-event-read'
    EVENT_UPDATE = 'bg-event-update'
    EVENT_DELETE = 'bg-event-delete'
    INSTANCE_CREATE = 'bg-instance-create'
    INSTANCE_READ = 'bg-instance-read'
    INSTANCE_UPDATE = 'bg-instance-update'
    INSTANCE_DELETE = 'bg-instance-delete'
    QUEUE_CREATE = 'bg-queue-create'
    QUEUE_READ = 'bg-queue-read'
    QUEUE_UPDATE = 'bg-queue-update'
    QUEUE_DELETE = 'bg-queue-delete'
    JOB_CREATE = 'bg-job-create'
    JOB_READ = 'bg-job-read'
    JOB_UPDATE = 'bg-job-update'
    JOB_DELETE = 'bg-job-delete'
    REQUEST_CREATE = 'bg-request-create'
    REQUEST_READ = 'bg-request-read'
    REQUEST_UPDATE = 'bg-request-update'
    REQUEST_DELETE = 'bg-request-delete'
    ROLE_CREATE = 'bg-role-create'
    ROLE_READ = 'bg-role-read'
    ROLE_UPDATE = 'bg-role-update'
    ROLE_DELETE = 'bg-role-delete'
    SYSTEM_CREATE = 'bg-system-create'
    SYSTEM_READ = 'bg-system-read'
    SYSTEM_UPDATE = 'bg-system-update'
    SYSTEM_DELETE = 'bg-system-delete'
    USER_CREATE = 'bg-user-create'
    USER_READ = 'bg-user-read'
    USER_UPDATE = 'bg-user-update'
    USER_DELETE = 'bg-user-delete'


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
        if principal == brew_view.anonymous_principal:
            raise HTTPError(status_code=401)
        else:
            raise RequestForbidden('Action requires permissions %s' %
                                   permission_strings)


def anonymous_principal():
    """Load correct anonymous permissions

    This exists in a weird space. We need to set the roles attribute to a 'real'
    Role object so it works correctly when the REST handler goes to serialize
    this principal.

    However, we also need to set the permissions attribute to the consolidated
    permission list so that ``check_permission`` will be able to do a comparison
    without having to calculate effective permissions every time.
    """

    if brew_view.config.auth.enabled:
        roles = Principal.objects.get(username='anonymous').roles
    else:
        roles = [Role(name='bg-admin', permissions=['bg-all'])]

    _, permissions = coalesce_permissions(roles)

    return BrewtilsPrincipal(
        username='anonymous', roles=roles, permissions=permissions)


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


def basic_auth(request):
    """Determine if a basic authorization header is valid

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if auth_header is valid, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return None

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


def bearer_auth(request):
    """Determine a principal from a JWT in the Authorization header

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]

    return _principal_from_token(token)


def query_token_auth(request):
    """Determine a principal from a JWT in query parameter 'token'

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    token_args = request.query_arguments.get('token', None)
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
    try:
        decoded = jwt.decode(token,
                             key=brew_view.config.auth.token.secret,
                             algorithm=brew_view.config.auth.token.algorithm)
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPError(status_code=401, log_message='Signature expired')

    return BrewtilsPrincipal(
        id=decoded['sub'],
        username=decoded.get('username', ''),
        roles=[BrewtilsRole(name=role) for role in decoded.get('roles', [])],
        permissions=decoded.get('permissions', [])
    )


class AuthMixin(object):

    auth_providers = [bearer_auth, basic_auth]

    def get_current_user(self):
        """Use registered handlers to determine current user"""

        for provider in self.auth_providers:
            principal = provider(self.request)

            if principal is not None:
                return principal

        return brew_view.anonymous_principal
