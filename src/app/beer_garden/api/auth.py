from enum import Enum

import wrapt
from brewtils.errors import RequestForbidden


class Permissions(Enum):
    ALL = "bg-all"
    COMMAND_CREATE = "bg-command-create"
    COMMAND_READ = "bg-command-read"
    COMMAND_UPDATE = "bg-command-update"
    COMMAND_DELETE = "bg-command-delete"
    EVENT_CREATE = "bg-event-create"
    EVENT_READ = "bg-event-read"
    EVENT_UPDATE = "bg-event-update"
    EVENT_DELETE = "bg-event-delete"
    INSTANCE_CREATE = "bg-instance-create"
    INSTANCE_READ = "bg-instance-read"
    INSTANCE_UPDATE = "bg-instance-update"
    INSTANCE_DELETE = "bg-instance-delete"
    QUEUE_CREATE = "bg-queue-create"
    QUEUE_READ = "bg-queue-read"
    QUEUE_UPDATE = "bg-queue-update"
    QUEUE_DELETE = "bg-queue-delete"
    JOB_CREATE = "bg-job-create"
    JOB_READ = "bg-job-read"
    JOB_UPDATE = "bg-job-update"
    JOB_DELETE = "bg-job-delete"
    REQUEST_CREATE = "bg-request-create"
    REQUEST_READ = "bg-request-read"
    REQUEST_UPDATE = "bg-request-update"
    REQUEST_DELETE = "bg-request-delete"
    ROLE_CREATE = "bg-role-create"
    ROLE_READ = "bg-role-read"
    ROLE_UPDATE = "bg-role-update"
    ROLE_DELETE = "bg-role-delete"
    SYSTEM_CREATE = "bg-system-create"
    SYSTEM_READ = "bg-system-read"
    SYSTEM_UPDATE = "bg-system-update"
    SYSTEM_DELETE = "bg-system-delete"
    USER_CREATE = "bg-user-create"
    USER_READ = "bg-user-read"
    USER_UPDATE = "bg-user-update"
    USER_DELETE = "bg-user-delete"


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
        # TODO - DONT THINK SO
        # Need to make a distinction between "you need to be authenticated
        # to do this" and "you've been authenticated and denied"
        # if principal == beer_garden.api.http.anonymous_principal:
        #     raise HTTPError(status_code=401)
        # else:
        raise RequestForbidden(f"Action requires permissions {permission_strings}")


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
