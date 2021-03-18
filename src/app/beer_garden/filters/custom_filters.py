from beer_garden import config
from beer_garden.filters.permission_mapper import PermissionRequiredAccess, Permissions
from brewtils.errors import AuthorizationRequired
from brewtils.models import Principal, Operation, Garden

"""
Any custom filters must be sure to not impact the Namespace/Garden filtering. If a field is filtered our at this level,
it will impact further checks. So be conscious on what you remove here.
"""


def principal_filtering(
    obj: Principal = None, raise_error: bool = True, current_user: Principal = None
):
    """
    Local Admins can edit any User account
    Current User can only edit their account

    Args:
        obj: Principal model to be modified
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation

    Returns:

    """

    if obj.id == current_user.id:
        return obj

    for permission in current_user.permissions:
        if (
            permission.access in PermissionRequiredAccess[Permissions.LOCAL_ADMIN]
            and permission.garden == config.get("garden.name")
            and permission.namespace is None
        ):
            return obj

    if raise_error:
        raise AuthorizationRequired(
            "Action Local Garden Admin permissions or be the user being modified in the request"
        )

    return None


def operation_filtering(
    obj: Operation = None, raise_error: bool = True, current_user: Principal = None
):
    """
    Local Admins can edit any User account
    Current User can only edit their account

    Args:
        obj: Operation model to be modified
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation

    Returns:

    """

    if obj.operation_type == "USER_UPDATE":
        if current_user.id == obj.kwargs["user_id"]:
            return obj

        for permission in current_user.permissions:

            # Scope = Local Admins must have Admin over just the Garden
            if (
                permission.access in PermissionRequiredAccess[Permissions.LOCAL_ADMIN]
                and permission.garden == config.get("garden.name")
                and permission.namespace is None
            ):
                return obj

        if raise_error:
            raise AuthorizationRequired(
                "Action Local Garden Admin permissions or be the user being modified in the request"
            )

        return None

    elif obj.operation_type in ["USER_UPDATE_ROLE", "USER_REMOVE_ROLE"]:
        for permission in current_user.permissions:

            # Scope = Local Admins must have Admin over just the Garden
            if (
                permission.access in PermissionRequiredAccess[Permissions.LOCAL_ADMIN]
                and permission.garden == config.get("garden.name")
                and permission.namespace is None
            ):
                return obj

        if raise_error:
            raise AuthorizationRequired(
                "Action Local Garden Admin permissions or be the user being modified in the request"
            )

        return None

    return obj


def garden_filtering(
    obj: Garden = None, raise_error: bool = True, current_user: Principal = None
):
    """
    Garden admins can return connection information.
    Garden Read access can return non Garden connection information.

    Args:
        obj: Garden model to be modified
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation

    Returns:

    """

    read_access = False

    # Loop through all permission to determine if the user has Admin permissions
    for permission in current_user.permissions:
        if (
            permission.access in PermissionRequiredAccess[Permissions.ADMIN]
            and permission.garden == obj.name
        ):
            return obj
        elif (
            permission.access in PermissionRequiredAccess[Permissions.LOCAL_ADMIN]
            and permission.garden == config.get("garden.name")
            and permission.namespace is None
        ):
            return obj
        elif (
            permission.access in PermissionRequiredAccess[Permissions.READ]
            and permission.garden == obj.name
        ):
            read_access = True

    # If Read Access was found, then remove the Connection Parameters
    if read_access:
        obj.connection_params = None
        return obj

    if raise_error:
        raise AuthorizationRequired("Action requires Garden permissions")

    return None


obj_custom_filtering = {
    Operation: operation_filtering,
    Principal: principal_filtering,
    Garden: garden_filtering,
}


def model_custom_filter(
    obj=None,
    raise_error: bool = True,
    current_user: Principal = None,
):
    """
    Filters the Brewtils Model based on specific rules
    Args:
        obj: Brewtils model to Filter
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation

    Returns:

    """

    # Impossible to add filters, so we return the object
    if not hasattr(obj, "schema"):
        return obj

    if type(obj) in obj_custom_filtering.keys():
        return obj_custom_filtering[type(obj)](
            obj=obj, raise_error=raise_error, current_user=current_user
        )

    return obj
