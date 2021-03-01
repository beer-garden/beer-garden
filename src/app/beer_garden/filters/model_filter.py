import logging

from beer_garden import config
from beer_garden.filters.permission_mapper import Permissions, PermissionRequiredAccess
from beer_garden.filters.garden_namespace_mapper import (
    find_obj_garden_namespace,
    obj_namespace_mapping,
)
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
        required_permission: Required permission defined for API

    Returns:

    """

    # First we check if we have an easy mapping to the namespace
    obj_garden, obj_namespace = find_obj_garden_namespace(obj)

    # If we find a namespace or garden, we can run the filter at this point
    if obj_namespace or obj_garden:
        if permission_check(
            garden=obj_garden,
            namespace=obj_namespace,
            current_user=current_user,
            required_permission=required_permission,
        ):
            # Now loop through to determine if any of the nested objects need to be filtered
            # This will also help future proof us for more complex objects
            for key in obj.__dict__.keys():

                # Run filter if we think we can actually filter the value
                if (
                    type(obj.__dict__[key]) == list
                    or type(obj.__dict__[key]) in obj_namespace_mapping.keys()
                ):
                    obj.__dict__[key] = model_filter(
                        obj=obj.__dict__[key],
                        raise_error=False,
                        current_user=current_user,
                        required_permission=required_permission,
                    )
            return obj
        if raise_error:
            raise AuthorizationRequired(
                "Action requires permissions for Garden = %s and Namespace = %s, currently has %s"
                % (obj_garden, obj_namespace, current_user.permissions)
            )

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

    if not required_permission or not config.get("auth.enabled"):
        return obj

    if not current_user:
        raise AuthorizationRequired("Action requires the User to be logged in")

    # Local Garden Admins get everything by default
    for permission in current_user.permissions:
        if (
            permission.garden == config.get("garden.name")
            and permission.access == "ADMIN"
            and permission.namespace is None
        ):
            return obj

    if type(obj) == list:
        new_obj = list()
        for obj_item in obj:
            # For list objects, we will not raise an error message
            obj_item = model_filter(
                obj=obj_item,
                raise_error=False,
                current_user=current_user,
                required_permission=required_permission,
            )
            if obj_item:
                new_obj.append(obj_item)
        return new_obj

    # Last ditch effort to verify they at least have the required permissions
    if type(obj) not in obj_namespace_mapping.keys():
        if permission_check(
            current_user=current_user, required_permission=required_permission
        ):
            return obj
        if raise_error:
            raise AuthorizationRequired("Action requires permissions")

        return None

    return filter_brewtils_model(
        obj=obj,
        raise_error=raise_error,
        current_user=current_user,
        required_permission=required_permission,
    )


def permission_check(
    namespace: str = None,
    garden: str = None,
    current_user: Principal = None,
    required_permission: Permissions = None,
):
    """
    Compares the namespace provided with the Principals permissions and required permissions
    Args:
        garden: Garden associated with Model
        namespace: Namespace associated with Model
        current_user: Principal record associated with the Model
        required_permission: Required permission level for the Model

    Returns:

    """
    for permission in current_user.permissions:

        # Scope = Local Admins must have Admin over just the Garden
        # TODO: Should this allow Garden + Namespace Admins to run?
        if (
            required_permission == Permissions.LOCAL_ADMIN
            and permission.access in PermissionRequiredAccess[required_permission]
            and permission.garden == config.get("garden.name")
            and permission.namespace is None
        ):
            return True

        elif required_permission == Permissions.LOCAL_ADMIN:
            return False

        # Scope = Has Access to everything within the Garden
        # Must have arg Garden to compare against
        elif (
            permission.namespace is None
            and garden is not None
            and permission.garden == garden
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        # Scope = Has access to everything within the Namespace
        # Must have arg Namespace to compare against
        elif (
            permission.garden is None
            and namespace is not None
            and permission.namespace == namespace
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        # Scope = Has access to everything within the intersect of Garden and Namespace
        # Must have args Garden and Namespace to compare against
        elif (
            garden is not None
            and namespace is not None
            and permission.garden == garden
            and permission.namespace == namespace
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        # Scope = Has access to everything within the intersect of Garden and Namespace, but only half is provided
        # If arg Garden is None but Permission Garden is set
        elif (
            garden is None
            and namespace is not None
            and permission.garden is not None
            and permission.namespace == namespace
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        # Scope = Has access to everything within the intersect of Garden and Namespace, but only half is provided
        # If arg Namespace is None but Permission Namespace is set
        elif (
            garden is not None
            and namespace is None
            and permission.garden == garden
            and permission.namespace is not None
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        # Scope = Unknown Target Garden/Namespace, but has level of access required
        elif (
            garden is None
            and namespace is None
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

        # Scope = Unknown Target Garden, but has level of access in Host Garden
        # If there is a namespace without a Garden, this has a high probability of a
        # entity creating a new Namespace, so they must have access to the Local Garden
        elif (
            garden is None
            and namespace is not None
            and permission.namespace is None
            and permission.garden == config.get("garden.name")
            and permission.access in PermissionRequiredAccess[required_permission]
        ):
            return True

    return False
