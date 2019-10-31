# -*- coding: utf-8 -*-
from typing import List, Sequence

from brewtils.errors import ModelValidationError
from brewtils.models import Principal, PatchOperation, Role
from passlib.apps import custom_app_context

import beer_garden.db.api as db
import beer_garden.db.mongo.models as mongo
from beer_garden.db.mongo.api import to_brewtils


def get_user(user_id: str = None, user_name: str = None) -> Principal:
    """Retrieve an individual User

    Args:
        user_id: The User ID
        user_name: The User name

    Returns:
        The User

    """
    query_kwargs = {}
    if user_id:
        query_kwargs["id"] = user_id
    if user_name:
        query_kwargs["username"] = user_name

    return db.query_unique(Principal, **query_kwargs)


def get_users(**kwargs) -> List[Principal]:
    """Search for Users

    Keyword Args:
        Parameters to be passed to the DB query

    Returns:
        The list of Users that matched the query

    """
    return db.query(Principal, **kwargs)


def create_user(user_name: str, password: str) -> Principal:
    """Create a new User

    Args:
        user_name: The name for the new user
        password: The raw (unhashed) password for the new user

    Returns:
        The created User

    """
    # TODO - Our brewtils model doesn't match up with the Mongo one
    new_user = mongo.Principal(
        username=user_name, hash=custom_app_context.hash(password)
    )
    new_user.save()

    return to_brewtils(new_user)


def update_user(user_id: str, operations: Sequence[PatchOperation]) -> Principal:
    """Update an already existing Principal

    Args:
        user_id: The ID of the Principal to be updated
        operations: List of patch operations

    Returns:
        The updated Principal

    """
    user = db.query_unique(Principal, id=user_id)

    for op in operations:
        if op.path == "/roles":

            # Updating roles always requires USER_UPDATE
            # check_permission(self.current_user, [Permissions.USER_UPDATE])

            if op.operation == "add":
                role = db.query_unique(Role, name=op.value)
                if role is None:
                    raise ModelValidationError(f"Unknown role '{op.value}'")
                user.roles.append(role)

            elif op.operation == "remove":
                role = db.query_unique(Role, name=op.value)
                if role is None:
                    raise ModelValidationError(f"Unknown role '{op.value}'")
                user.roles.remove(role)

            elif op.operation == "set":
                user.roles = []

                for name in op.value:
                    role = db.query_unique(Role, name=name)
                    if role is None:
                        raise ModelValidationError(f"Unknown role '{name}'")
                    user.roles.append(role)

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

            user = db.update(user)

        elif op.path == "/username":
            if op.operation == "update":
                user.username = op.value
                user = db.update(user)
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        # elif op.path == "/password":
        #     if op.operation != "update":
        #         raise ModelValidationError(f"Unsupported operation '{op.operation}'")
        #
        #     if isinstance(op.value, dict):
        #         current_password = op.value.get("current_password")
        #         new_password = op.value.get("new_password")
        #     else:
        #         current_password = None
        #         new_password = op.value
        #
        #     if user_id == str(self.current_user.id):
        #         if current_password is None:
        #             raise ModelValidationError(
        #                 "In order to update your own password, you must provide "
        #                 "your current password"
        #             )
        #
        #         if not custom_app_context.verify(
        #                 current_password, self.current_user.hash
        #         ):
        #             raise RequestForbidden("Invalid password")
        #
        #     principal.hash = custom_app_context.hash(new_password)
        #     if "changed" in principal.metadata:
        #         principal.metadata["changed"] = True

        elif op.path == "/preferences/theme":
            if op.operation == "set":
                user.preferences["theme"] = op.value
                user = db.update(user)
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        else:
            raise ModelValidationError("Unsupported path '%s'" % op.path)

    return user


def remove_user(user_id: str):
    """Removes a User

    Args:
        user_id: The User ID

    Returns:
        None
    """
    db.delete(db.query_unique(Principal, id=user_id))
