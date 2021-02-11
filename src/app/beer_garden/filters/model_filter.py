import logging

from beer_garden.filters.permission_mapper import Permissions, PermissionRequiredAccess
from beer_garden.filters.namespace_mapper import find_obj_namespace
from brewtils.errors import AuthorizationRequired
from brewtils.models import (
    Principal,
)

logger = logging.getLogger(__name__)

"""
Just some notes for future self:

Long term we are going to want to add tag filtering. Projecting that these will be on
both commands and systems. So when returning a System, we will have to run through all
commands and only return the ones approved.

We will also want to roll the tags upwards. So a System will have all the tags associated
with it, and the commands. So if the System object doesn't have any of the proper tags
then don't return it.

We will also need to add the tags of the Command to the Request record, so we can filter
on that as well. This will need to work for the Request Template as well. If the
developer changes the tags on a command, historic commands should maintain their original
tags.

Also, if a user is approved of the Namespace OR Tag, then the object is returned. We
want the least restrictive approach.
"""


def filter_brewtils_model(
    obj=None,
    raise_error: bool = True,
    current_user: Principal = None,
    required_permission: Permissions = None,
):
    """
    Filters the Brewtils Model
    Args:
        obj: Brewtils model to Filter
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation
        required_permissions: Required permissions defined for API

    Returns:

    """

    # Last ditch effort to verify they at least have the required permissions
    if not hasattr(obj, "schema"):
        if permission_check(
            current_user=current_user, required_permission=required_permission
        ):
            return obj
        if raise_error:
            raise AuthorizationRequired("Action requires permissions")

        return None

    # First we check if we have an easy mapping to the namespace
    obj_namespace = find_obj_namespace(obj)

    # If we find a namespace, we can run the filter at this point
    if obj_namespace:
        if permission_check(
            namespace=obj_namespace,
            current_user=current_user,
            required_permission=required_permission,
        ):
            return obj
        if raise_error:
            raise AuthorizationRequired("Action requires permissions %s" % obj_namespace)

        return None

    # We have no way to filter, we will return the obj for now and log an error
    # This should be removed long term, this is here to make sure we know a schema wasn't
    # captured.
    logger.debug(f"Unable to filter obj for schema type {obj.schema}")

    return obj


def model_filter(
    obj=None,
    raise_error: bool = True,
    current_user: Principal = None,
    required_permission: Permissions = None,
):
    """
    Filters a Model
    Args:
        obj: Model to Filter
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation
        required_permission: Required permissions defined for API

    Returns:

    """

    if not required_permission:
        return obj

    if not current_user:
        raise AuthorizationRequired("Action requires the User to be logged in")

    # Local Admins get everything by default
    for permission in current_user.permissions:
        if permission.is_local and permission.access == "ADMIN":
            return obj

    if type(obj) == list:
        new_obj = list()
        for obj_item in obj:
            # For list objects, we will not raise an error message
            obj_item = filter_brewtils_model(
                obj=obj_item,
                raise_error=False,
                current_user=current_user,
                required_permission=required_permission,
            )
            if obj_item:
                new_obj.append(obj_item)
        return new_obj

    return filter_brewtils_model(
        obj=obj,
        raise_error=raise_error,
        current_user=current_user,
        required_permission=required_permission,
    )


def permission_check(
    namespace: str = None,
    current_user: Principal = None,
    required_permission: Permissions = None,
):
    """
    Compares the namespace provided with the Principals permissions and required permissions
    Args:
        namespace: Namespace associated with Model
        current_user: Principal record associated with the Model
        required_permission: Required permission level for the Model

    Returns:

    """
    for permission in current_user.permissions:
        if (
            required_permission == Permissions.LOCAL_ADMIN
            and permission.is_local
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        if permission.access in PermissionRequiredAccess[required_permission] and (
            namespace is None
            or permission.namespace == namespace
            or permission.is_local
        ):
            return True

    return False
