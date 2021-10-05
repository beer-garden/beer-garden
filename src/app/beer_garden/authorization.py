from typing import TYPE_CHECKING, Optional, Type

from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Job as BrewtilsJob
from brewtils.models import Request as BrewtilsRequest
from brewtils.models import System as BrewtilsSystem
from bson import ObjectId
from mongoengine import Document, DoesNotExist, Q, QuerySet

import beer_garden.db.mongo.models
from beer_garden.db.mongo.models import (
    Garden,
    Job,
    Request,
    RoleAssignmentDomain,
    System,
)

if TYPE_CHECKING:
    from beer_garden.db.mongo.models import User


_types_that_derive_system_from_request = [Job, BrewtilsJob, Request, BrewtilsRequest]


def permissions_for_user(user: "User") -> dict:
    """Generates a dict containing the user's permissions organized by permission and
    listing the domains in which the user holds that permission based on their current
    role_assignments. The final output will look something like:

    {
        "garden:read": {
            "garden_ids": ["61391177f150fcc57019d48f", "61391177f150fcc57062338a"]
            "system_ids": []
        },
        "request:create": {
            "garden_ids": ["61391177f150fcc57019d48f"],
            "system_ids": ["61391187766f458bf9625905", "613911898c962bcacc470279"]
        }
    }

    Args:
        user: User for which to calculate the permissions

    Returns:
        dict: Dictionary formatted as described above
    """
    user_permissions = {}

    for role_assignment in user.role_assignments:
        permissions = role_assignment.role.permissions

        for permission in permissions:
            if permission not in user_permissions.keys():
                user_permissions[permission] = {"garden_ids": [], "system_ids": []}

            domain_object_ids = _get_object_ids_from_domain(role_assignment.domain)

            permission_key = f"{role_assignment.domain.scope.lower()}_ids"

            object_ids_to_add = [
                object_id
                for object_id in domain_object_ids
                if object_id not in user_permissions[permission][permission_key]
            ]
            user_permissions[permission][permission_key].extend(object_ids_to_add)

    return user_permissions


def user_has_permission_for_object(user: "User", permission: str, obj) -> bool:
    """Determines if the supplied user has a specified permission for a given object

    Args:
        user: The User to check the permissions of
        permission: The permission to check against
        obj: The object to check against. This could be either a brewtils model or
             a mongoengine Document model object.

    Returns:
        bool: True if the user has the specified permission for the object.
              False otherwise.
    """
    permitted_domains = user.permissions.get(permission, None)

    if permitted_domains is None:
        return False

    permitted_garden_ids = permitted_domains["garden_ids"]
    permitted_system_ids = permitted_domains["system_ids"]

    return (
        _get_object_garden_id(obj) in permitted_garden_ids
        or _get_object_system_id(obj) in permitted_system_ids
    )


def user_permitted_objects(
    user: "User", model: Type[Document], permission: str
) -> QuerySet:
    """Generates a QuerySet filtered down to the objects for which the user has the
    given permission

    Args:
        user: The User whose permissions will be used as the basis for filtering
        model: The mongo Document model class to generate a QuerySet for
        permission: The permission that the user must have in order to be permitted
            access to the object

    Returns:
        QuerySet: A mongo QuerySet filtered down to the objects the user has access to
    """
    permitted_domains = user.permissions.get(permission)

    if permitted_domains is None:
        return model.objects.none()

    garden_filter = _get_garden_filter(model, permitted_domains["garden_ids"])
    system_filter = _get_system_filter(model, permitted_domains["system_ids"])

    return model.objects.filter(garden_filter | system_filter)


def _get_garden_filter(model: Type[Document], garden_ids: list) -> Q:
    """Returns a Q filter object for filtering a queryset by a list of garden ids"""
    garden_name_field = _get_garden_name_field(model)
    garden_names = Garden.objects.filter(id__in=garden_ids).values_list("name")

    return Q(**{f"{garden_name_field}__in": garden_names})


def _get_system_filter(model: Type[Document], system_ids: list) -> Q:
    """Returns a Q filter object for filtering a queryset by a list of system ids"""
    if model == System:
        q_filter = Q(id__in=system_ids)
    elif model in _types_that_derive_system_from_request:
        q_filter = Q()

        systems = System.objects.filter(id__in=system_ids)

        if hasattr(model, "request_template"):
            field_prefix = "request_template__"
        else:
            field_prefix = ""

        for system in systems:
            q_filter = q_filter | Q(
                **{
                    f"{field_prefix}system": system.name,
                    f"{field_prefix}system_version": system.version,
                    f"{field_prefix}namespace": system.namespace,
                }
            )
    else:
        q_filter = Q()

    return q_filter


def _get_garden_name_field(model: Type[Document]):
    """Returns the name of the model field that corresponds to garden name"""
    field_name_map = {
        "Garden": "name",
        "Job": "request_template__namespace",
        "Request": "namespace",
        "System": "namespace",
    }

    return field_name_map.get(model.__name__)


def _get_object_ids_from_domain(domain: RoleAssignmentDomain) -> list:
    """Retrieve the object ids (as strings) that correspond to the given domain"""
    model = getattr(beer_garden.db.mongo.models, domain.scope)
    model_objects = model.objects.filter(**domain.identifiers)

    return [str(object_id) for object_id in model_objects.values_list("id")]


def _get_garden_id_from_namespace(obj) -> Optional[ObjectId]:
    """Returns the Garden id corresponding to the supplied object based on the namespace
    field from the object or its request_template
    """
    obj_with_namespace = getattr(obj, "request_template", None) or obj
    namespace = getattr(obj_with_namespace, "namespace", None)

    if namespace:
        try:
            garden_id = Garden.objects.get(name=namespace).id
        except DoesNotExist:
            garden_id = None
    else:
        garden_id = None

    return garden_id


def _get_system_id_from_request(obj) -> Optional[ObjectId]:
    """Returns the System id corresponding to the supplied object based on the fields
    representing a system on the object or its request_template (i.e system, version,
    and namespace)
    """
    obj_with_system = getattr(obj, "request_template", None) or obj

    try:
        system_id = System.objects.get(
            name=obj_with_system.system,
            version=obj_with_system.system_version,
            namespace=obj_with_system.namespace,
        ).id
    except DoesNotExist:
        system_id = None

    return system_id


def _get_object_garden_id(obj) -> Optional[str]:
    """Finds the Garden id (as a string) for the supplied object"""
    garden_id = None

    if isinstance(obj, Garden):
        garden_id = obj.id
    elif isinstance(obj, BrewtilsGarden):
        garden_id = ObjectId(obj.id)
    else:
        garden_id = _get_garden_id_from_namespace(obj)

    return str(garden_id) if garden_id else None


def _get_object_system_id(obj) -> Optional[str]:
    """Finds the System id (as a string) for the supplied object"""
    system_id = None

    if isinstance(obj, System):
        system_id = obj.id
    elif isinstance(obj, BrewtilsSystem):
        system_id = ObjectId(obj.id)
    elif type(obj) in _types_that_derive_system_from_request:
        system_id = _get_system_id_from_request(obj)

    return str(system_id) if system_id else None
