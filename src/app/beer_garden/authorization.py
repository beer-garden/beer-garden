from typing import Union
import logging
# from typing import TYPE_CHECKING, Optional, Type, Union

from brewtils.models import BaseModel as BrewtilsModel
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Job as BrewtilsJob
from brewtils.models import Request as BrewtilsRequest
from brewtils.models import RequestTemplate as BrewtilsRequestTemplate
from brewtils.models import System as BrewtilsSystem
from brewtils.models import User as BrewtilsUser
from brewtils.models import Role as BrewtilsRole
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import Event as BrewtilsEvent
from mongoengine import Q
import beer_garden.config as config

# from mongoengine import Document, DoesNaotExist, Q, QuerySet
# from mongoengine.fields import ObjectIdField
# from mongoengine.queryset.visitor import QCombination

# import beer_garden.db.mongo.models
# from beer_garden.api.authorization import Permissions
# from beer_garden.db.mongo.models import (
#     Garden,
#     Job,
#     Request,
#     System,
# )

import beer_garden.db.api as db
logger = logging.getLogger(__name__)

def check_global_roles(
    user: BrewtilsUser,
    permission_level: str = None,
    permission_levels: list = None,
) -> bool:
    if permission_levels is None:
        permission_levels = generate_permission_levels(permission_level)

    for roles in [user.local_roles if user.local_roles else [], user.remote_roles if user.remote_roles else []]:
        if any(
            role.permission in permission_levels and _has_empty_scopes(role)
            for role in roles
        ):
            return True
        
        # Check is the user has Garden Admin for the current Garden
        if any(
            role.permission == "GARDEN_ADMIN" and (
                    len(role.scope_gardens) == 0 or config.get("garden.name") in role.scope_gardens
                ) 
            for role in roles
        ):
            return True

    return False


def generate_permission_levels(permission_level: str) -> list:
    if permission_level == "READ_ONLY":
        return ["READ_ONLY", "OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"]

    if permission_level == "OPERATOR":
        return ["OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"]
    
    if permission_level == "PLUGIN_ADMIN":
        return ["PLUGIN_ADMIN", "GARDEN_ADMIN"]
    
    if permission_level == "GARDEN_ADMIN":
        return ["GARDEN_ADMIN"]
    
    return []


def _has_empty_scopes(
    role: BrewtilsRole,
    scopes: list = [
        "scope_gardens",
        "scope_namespaces",
        "scope_systems",
        "scope_instances",
        "scope_versions",
        "scope_commands",
    ],
):
    for scope_attribute in scopes:
        if len(getattr(role, scope_attribute, [])) > 0:
            return False
    return True


class QueryFilterBuilder:
    def _get_garden_q_filter(self, user: BrewtilsUser, permission_levels: list) -> Q:
        """Returns a Q filter object for filtering a queryset for gardens"""

        if check_global_roles(user, permission_levels=permission_levels):
            return Q()

        garden_names = []
        for roles in [user.local_roles, user.remote_roles]:
            for role in roles:
                if role in permission_levels:
                    for garden_scope in role.scope_gardens:
                        garden_names.append(garden_scope)

        return Q(**{"name__in": garden_names})

    def _get_system_filter(self, user: BrewtilsUser, permission_levels: list) -> Q:
        if check_global_roles(user, permission_levels=permission_levels):
            return Q()

        filters = []

        for roles in [user.local_roles, user.remote_roles]:
            for role in roles:
                if role in permission_levels:
                    filter = {}
                    if len(role.systems) > 0:
                        filter["name_in"] = role.systems
                    if len(role.instances) > 0:
                        filter["instances__name__in"] = role.instances
                    if len(role.versions) > 0:
                        filter["version__in"] = role.versions
                    if len(role.commands) > 0:
                        filter["commands__name__in"] = role.commands

                    if len(filter) > 0:
                        filters.append(Q**filter)

        if len(filters) == 0:
            return Q()

        output = None

        for filter in filters:
            if output is None:
                output = filter
            else:
                output = output | filter

        return output

    def _get_instance_filter(self, user: BrewtilsUser, permission_levels: list) -> Q:
        if check_global_roles(user, permission_levels=permission_levels):
            return Q()

        filters = []

        for roles in [user.local_roles, user.remote_roles]:
            for role in roles:
                if role in permission_levels:
                    filter = {}
                    if len(role.instances) > 0:
                        filter["name__in"] = role.instances

                    if len(filter) > 0:
                        filters.append(Q**filter)

        if len(filters) == 0:
            return Q()

        output = None

        for filter in filters:
            if output is None:
                output = filter
            else:
                output = output | filter

        return output

    def build_filter(
        self, user: BrewtilsUser, permission: str, model: BrewtilsModel, **kwargs
    ) -> Q:
        permission_levels = generate_permission_levels(permission)

        if len(user.local_roles) == 0 and len(user.remote_roles) == 0:
            return None

        if model is None:
            return Q()

        if model is BrewtilsGarden:
            return self._get_garden_q_filter(user, permission_levels)
        if model is BrewtilsSystem:
            return self._get_system_filter(user, permission_levels)
        if model is BrewtilsInstance:
            return self._get_instance_filter(user, permission_levels)

        return Q()


class ModelFilter:
    def _checks(
        self,
        user: BrewtilsUser,
        permission: str = None,
        permission_levels: list = None,
        check_garden: bool = False,
        check_system: bool = False,
        check_namespace: bool = False,
        check_instances: bool = False,
        check_version: bool = False,
        check_command: bool = False,
        garden_name: str = None,
        system: BrewtilsSystem = None,
        system_id: str = None,
        system_name: str = None,
        system_namespace: str = None,
        system_version: str = None,
        system_instances: list = None,
        instance_id: str = None,
        command_name: str = None,
    ):
        """Core check for filtering. If provided a nested record with some parent attributes, 
        attempt to find it's source for the checks. If None is provided, then skip the check 
        because we can't determine the value"""

        if not permission_levels and permission:
            permission_levels = generate_permission_levels(permission)

        if system is None:
            if (
                (check_system and system_name is None)
                or (check_namespace and system_namespace is None)
                or (check_instances and system_instances is None)
                or (check_version and system_version is None)
                or (check_garden and (garden_name is None or system_name is None))
            ):
                if system_id:
                    system = db.query_unique(
                        BrewtilsSystem, id=system_id, raise_missing=True
                    )
                elif system_name and system_namespace and system_version:
                    system = db.query_unique(
                        BrewtilsSystem, name=system_name, version=system_version, namespace=system_namespace, raise_missing=True
                    )
                elif system_name:
                    system = db.query_unique(
                        BrewtilsSystem, name=system_name, raise_missing=True
                    )                 
                elif instance_id:
                    system = db.query_unique(
                        BrewtilsSystem, instances_id=instance_id, raise_missing=True
                    )
                
        if system:
            
            if check_system and system_name is None:
                system_name = system.name
            if check_instances and system_instances is None:
                system_instances = [i.name for i in system.instances]
            if check_version and system_version is None:
                system_version = system.version
            if check_namespace and system_namespace is None:
                system_namespace = system.namespace

        if system_name and check_garden and garden_name is None:
            if system:
                gardens = db.query(BrewtilsGarden, systems__id=system.id)

            if gardens and len(gardens) == 1:
                garden_name = gardens[0].name
            else:
                # TODO: Add better Exception
                raise Exception("Unable to find source garden for Authorization checks")

        for roles in [user.local_roles, user.remote_roles]:
            if any(
                (
                    role.permission in permission_levels
                    and (
                        not check_garden
                        or garden_name is None
                        or len(role.scope_gardens) == 0
                        or garden_name in role.scope_gardens
                    )
                    and (
                        not check_namespace
                        or system_namespace is None
                        or len(role.scope_namespaces) == 0
                        or system_namespace in role.scope_namespaces
                    )
                    and (
                        not check_system
                        or system_name is None
                        or system_name is None
                        or len(role.scope_systems) == 0
                        or system_name in role.scope_systems
                    )
                    and (
                        not check_version
                        or system_version is None
                        or len(role.scope_versions) == 0
                        or system_version in role.scope_versions
                    )
                    and (
                        not check_instances
                        or system_instances is None
                        or len(role.scope_instances) == 0
                        or any(
                            instance_name in role.scope_instances
                            for instance_name in system_instances
                        )
                    )
                    and (
                        not check_command
                        or command_name is None
                        or len(role.scope_commands) == 0
                        or command_name in role.scope_commands
                    )
                )
                for role in roles
            ):
                return True

            return False

    def _get_user_filter(
        self,
        user_output: BrewtilsUser,
        user: BrewtilsUser,
        permission_levels: list,
        skip_global: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered User object based on the roles of the user"""

        if user_output.username == user.username:
            return user_output

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return user_output

        if self._checks(user, permission_levels=permission_levels, **kwargs):
            return user_output

        return None

    def _get_role_filter(
        self,
        role: BrewtilsRole,
        user: BrewtilsUser,
        permission_levels: list,
        skip_global: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered User object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return role

        # Can return the role information, if the user has the role
        if role.name in user.roles:
            return role

        return None

    def _get_job_filter(
        self,
        job: BrewtilsJob,
        user: BrewtilsUser,
        permission_levels: list,
        source_garden: str = None,
        skip_global: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered Job object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return job

        filtered_request_template = self._get_request_filter(
            job.request_template,
            user,
            permission_levels,
            source_garden=source_garden,
            skip_global=True,
            **kwargs,
        )

        if filtered_request_template:
            return job

        return None

    def _get_request_filter(
        self,
        request: Union[BrewtilsRequest, BrewtilsRequestTemplate],
        user: BrewtilsUser,
        permission_levels: list,
        source_garden: str = None,
        skip_global: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered Job object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return request

        # Owner of the request can always see what they submitted
        if getattr(request, "requester", None) == user.username:
            return request

        if self._checks(
            user,
            permission_levels=permission_levels,
            garden_name=source_garden,
            system_namespace=request.namespace,
            system_name=request.system,
            system_version=request.system_version,
            system_instances=[request.instance_name],
            command_name=request.command,
            check_garden=True,
            check_system=True,
            check_namespace=True,
            check_version=True,
            check_instances=True,
            check_command=True,
            **kwargs,
        ):
            return request

        return None

    def _get_command_filter(
        self,
        command: BrewtilsCommand,
        user: BrewtilsUser,
        permission_levels: list,
        source_system: BrewtilsSystem = None,
        source_garden_name: str = None,
        source_system_namespace: str = None,
        source_system_name: str = None,
        source_system_instances: list = None,
        source_system_version: str = None,
        skip_global: bool = False,
        skip_system: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered Command object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return command

        if self._checks(
            user,
            permission_levels=permission_levels,
            garden_name=source_garden_name,
            system=source_system,
            system_namespace=source_system_namespace,
            system_name=source_system_name,
            system_version=source_system_version,
            system_instances=source_system_instances,
            command_name=command.name,
            check_garden=True,
            check_system=not skip_system,
            check_namespace=not skip_system,
            check_version=not skip_system,
            check_instances=not skip_system,
            check_command=True,
            **kwargs,
        ):
            return command

        return None

    def _get_instance_filter(
        self,
        instance: BrewtilsInstance,
        user: BrewtilsUser,
        permission_levels: list,
        source_system: BrewtilsSystem = None,
        source_garden_name: str = None,
        source_system_namespace: str = None,
        source_system_name: str = None,
        source_system_version: str = None,
        skip_global: bool = False,
        skip_system: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered Command object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return instance

        if self._checks(
            user,
            permission_levels=permission_levels,
            system=source_system,
            garden_name=source_garden_name,
            system_namespace=source_system_namespace,
            system_name=source_system_name,
            system_version=source_system_version,
            system_instances=[instance.name],
            check_garden=True,
            check_system=not skip_system,
            check_namespace=not skip_system,
            check_version=not skip_system,
            check_instances=True,
            instance_id=instance.id,
            **kwargs,
        ):
            return instance


        return None

    def _get_system_filter(
        self,
        system: BrewtilsSystem,
        user: BrewtilsUser,
        permission_levels: list,
        source_garden_name: str = None,
        skip_global: bool = False,
        **kwargs
    ) -> BrewtilsSystem:
        """Returns a filtered System object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return system

        if not self._checks(
            user,
            permission_levels=permission_levels,
            system=system,
            garden_name=source_garden_name,
            check_garden=True,
            check_system=True,
            check_namespace=True,
            check_version=True,
            **kwargs,
        ):
            return None

        filter_commands = True
        filter_instances = True
        for roles in [user.local_roles, user.remote_roles]:
            for role in roles:
                if (
                    (
                        source_garden_name is None
                        or len(role.scope_gardens) == 0
                        or source_garden_name in role.scope_gardens
                    )
                    and (
                        len(role.scope_systems) == 0
                        or system.name in role.scope_systems
                    )
                    and (
                        len(role.scope_namespaces) == 0
                        or system.namespace in role.scope_namespaces
                    )
                    and (
                        len(role.scope_versions) == 0
                        or system.version in role.scope_versions
                    )
                ):
                    if len(role.scope_commands) == 0:
                        filter_commands = False
                    if len(role.scope_instances) == 0:
                        filter_instances = False

                    if not filter_commands and not filter_instances:
                        break

        # Filter Instances
        if filter_instances and system.instances:
            filtered_instances = []
            for instance in system.instances:
                logger.error("Check Instance")
                filtered_instance = self._get_instance_filter(
                    instance,
                    user,
                    permission_levels,
                    source_garden_name=source_garden_name,
                    source_system=system,
                    skip_global=True,
                    skip_system=True,
                )
                
                if filtered_instance:
                    filtered_instances.append(filtered_instance)

            if len(filtered_instances) == 0:
                return None

            system.instances = filtered_instances

        filter_commands = True
        for roles in [user.local_roles, user.remote_roles]:
            for role in roles:
                if (
                    (
                        source_garden_name is None
                        or len(role.scope_gardens) == 0
                        or source_garden_name in role.scope_gardens
                    )
                    and (
                        len(role.scope_systems) == 0
                        or system.name in role.scope_systems
                    )
                    and (
                        len(role.scope_namespaces) == 0
                        or system.namespace in role.scope_namespaces
                    )
                    and (
                        len(role.scope_versions) == 0
                        or system.version in role.scope_versions
                    )
                    and len(role.scope_commands) == 0
                ):
                    filter_commands = False
                    break

        # Filter Commands
        if filter_commands and system.commands:
            filtered_commands = []
            for command in system.commands:
                filtered_command = self._get_command_filter(
                    command,
                    user,
                    permission_levels,
                    source_garden_name=source_garden_name,
                    source_system=system,
                    skip_global=True,
                    skip_system=True,
                )
                if filtered_command:
                    filtered_commands.append(filtered_command)

            if len(filtered_commands) == 0:
                return None

        return system

    def _get_garden_filter(
        self,
        garden: BrewtilsGarden,
        user: BrewtilsUser,
        permission_levels: list,
        skip_global: bool = False,
        **kwargs
    ) -> BrewtilsGarden:
        """Returns a filtered Garden object based on the roles of the user"""

        if not skip_global and check_global_roles(user, permission_levels=permission_levels):
            return garden

        if not self._checks(
            user,
            permission_levels=permission_levels,
            garden_name=garden.name,
            check_garden=True,
            **kwargs,
        ):
            return None

        if garden.systems:
            filter_systems = True
            for roles in [user.local_roles, user.remote_roles]:
                for role in roles:
                    if garden.name in role.scope_gardens and _has_empty_scopes(
                        role,
                        [
                            "scope_namespaces",
                            "scope_systems",
                            "scope_instances",
                            "scope_versions",
                            "scope_commands",
                        ],
                    ):
                        filter_systems = False
                        break

            if filter_systems:
                new_systems = []
                for system in garden.systems:
                    filtered_system = self._get_system_filter(
                        system,
                        user,
                        permission_levels,
                        source_garden_name=garden.name,
                        skip_global=True,
                    )
                    if filtered_system:
                        new_systems.append(filtered_system)

                garden.systems = filtered_system

        new_child_gardens = []
        if garden.children:
            for child in garden.children:
                filtered_garden = self._get_garden_filter(
                    child, user, permission_levels, skip_global=True
                )
                if filtered_garden:
                    new_child_gardens.append(filtered_garden)
            garden.children = new_child_gardens

        return garden

    def filter_object(
        self,
        obj: BrewtilsModel = None,
        user: BrewtilsUser = None,
        permission: str = None,
        permission_levels: list[str] = None,
        **kwargs
    ) -> BrewtilsModel:
        
        if not permission_levels:
            permission_levels = generate_permission_levels(permission)

        if isinstance(obj, list):
            outputList = []
            for value in obj:
                output = self.filter_object(
                    obj=value, user=user, permission_levels=permission_levels, **kwargs
                )
                if output:
                    outputList.append(output)

            return outputList

        if check_global_roles(user, permission_levels=permission_levels):
            return obj

        if obj is None:
            return None

        if isinstance(obj, BrewtilsGarden):
            return self._get_garden_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsSystem):
            return self._get_system_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsUser):
            return self._get_system_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsInstance):
            return self._get_instance_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsJob):
            return self._get_job_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsRequest):
            return self._get_request_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsUser):
            return self._get_user_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsRole):
            return self._get_role_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsEvent):
            if obj.payload:
                payload_filtered = self.filter_object(
                    user, obj.payload, permission_levels=permission_levels, **kwargs
                )
                if payload_filtered:
                    obj.payload = payload_filtered
                else:
                    return None

        # If object is outside of the filters, check for permissions at a minimum
        if check_global_roles(user, permission_levels=permission_levels):
            return obj


########################################
#            OLD STUFF                 #
########################################

# if TYPE_CHECKING:
#     from beer_garden.db.mongo.models import User

# OBJECT_OWNER_PERMISSIONS = [Permissions.REQUEST_READ.value]


# _types_that_derive_system_from_request = [Job, BrewtilsJob, Request, BrewtilsRequest]
# _model_username_field_map = {"Request": "requester"}


# def permissions_for_user(user: "User") -> dict:
#     """Generates a dict containing the user's permissions organized by permission and
#     listing the domains in which the user holds that permission based on their current
#     role_assignments. The final output will look something like:

#     {
#         "global_permissions": ["system:read", "request:read"],
#         "domain_permissions": {
#             "garden:read": {
#                 "garden_ids": ["61391177f150fcc57019d48f", "61391177f150fcc57062338a"]
#                 "system_ids": []
#             },
#             "request:create": {
#                 "garden_ids": ["61391177f150fcc57019d48f"],
#                 "system_ids": ["61391187766f458bf9625905", "613911898c962bcacc470279"]
#             }
#         }
#     }

#     Args:
#         user: User for which to calculate the permissions

#     Returns:
#         dict: Dictionary formatted as described above
#     """
#     global_permissions = []
#     domain_permissions = {}

#     for role_assignment in user.role_assignments:
#         permissions = role_assignment.role.permissions

#         if role_assignment.domain.scope == "Global":
#             global_permissions.extend(permissions)
#             continue

#         for permission in permissions:
#             if permission not in domain_permissions.keys():
#                 domain_permissions[permission] = {"garden_ids": [], "system_ids": []}

#             domain_object_ids = _get_object_ids_from_domain(role_assignment.domain)

#             permission_key = f"{role_assignment.domain.scope.lower()}_ids"

#             object_ids_to_add = [
#                 object_id
#                 for object_id in domain_object_ids
#                 if object_id not in domain_permissions[permission][permission_key]
#             ]
#             domain_permissions[permission][permission_key].extend(object_ids_to_add)

#     user_permissions = {
#         "global_permissions": list(set(global_permissions)),
#         "domain_permissions": domain_permissions,
#     }

#     return user_permissions


# def user_has_permission_for_object(
#     user: "User", permission: str, obj: Union[Document, BrewtilsModel]
# ) -> bool:
#     """Determines if the supplied user has a specified permission for a given object

#     Args:
#         user: The User to check the permissions of
#         permission: The permission to check against
#         obj: The object to check against. This could be either a brewtils model or
#              a mongoengine Document model object.

#     Returns:
#         bool: True if the user has the specified permission for the object.
#               False otherwise.

#     Raises:
#         TypeError: The provided object is of an unsupported type
#     """
#     if not (isinstance(obj, Document) or isinstance(obj, BrewtilsModel)):
#         raise TypeError("obj must be of a type derived from Document or BrewtilsModel")

#     if permission in user.global_permissions or _user_has_object_owner_permission(
#         user, permission, obj
#     ):
#         return True

#     permitted_domains = user.domain_permissions.get(permission, None)

#     if permitted_domains is None:
#         return False

#     permitted_garden_ids = permitted_domains["garden_ids"]
#     permitted_system_ids = permitted_domains["system_ids"]

#     return (
#         _get_object_garden_id(obj) in permitted_garden_ids
#         or _get_object_system_id(obj) in permitted_system_ids
#     )


# def user_permitted_objects(
#     user: "User", model: Type[Document], permission: str
# ) -> QuerySet:
#     """Generates a QuerySet filtered down to the objects for which the user has the
#     given permission

#     Args:
#         user: The User whose permissions will be used as the basis for filtering
#         model: The mongo Document model class to generate a QuerySet for
#         permission: The permission that the user must have in order to be permitted
#             access to the object

#     Returns:
#         QuerySet: A mongoengine QuerySet filtered to the objects the user has access to
#     """
#     q_filter = user_permitted_objects_filter(user, model, permission)

#     if q_filter is not None:
#         return model.objects.filter(q_filter)
#     else:
#         return model.objects.none()


# def user_permitted_objects_filter(
#     user: "User", model: Type[Document], permission: str
# ) -> Optional[Union[Q, QCombination]]:
#     """Generates a QCombination that can be used to filter a QuerySet down to the
#     objects for which the user has the given permission

#     Args:
#         user: The User whose permissions will be used as the basis for filtering
#         model: The mongoengine Document model class that access will be checked for
#         permission: The permission that the user must have in order to be permitted
#             access to the object

#     Returns:
#         Q: An empty mongoengine Q filter, representing global access
#         QCombination: A mongoengine QCombination filter
#         None: The user has access to no objects
#     """
#     if permission in user.global_permissions:
#         return Q()

#     permitted_domains = user.domain_permissions.get(permission)
#     q_filter = _get_user_filter(model, user)

#     if permitted_domains:
#         garden_filter = _get_garden_filter(model, permitted_domains["garden_ids"])
#         system_filter = _get_system_filter(model, permitted_domains["system_ids"])

#         q_filter = q_filter | garden_filter | system_filter

#     if q_filter:
#         return q_filter
#     else:
#         return None


# def _get_garden_filter(model: Type[Document], garden_ids: list) -> Q:
#     """Returns a Q filter object for filtering a queryset by a list of garden ids"""
#     garden_name_field = _get_garden_name_field(model)
#     garden_names = Garden.objects.filter(id__in=garden_ids).values_list("name")

#     return Q(**{f"{garden_name_field}__in": garden_names})


# def _get_system_filter(model: Type[Document], system_ids: list) -> Q:
#     """Returns a Q filter object for filtering a queryset by a list of system ids"""
#     if model == System:
#         q_filter = Q(id__in=system_ids)
#     elif model in _types_that_derive_system_from_request:
#         q_filter = Q()

#         systems = System.objects.filter(id__in=system_ids)

#         if hasattr(model, "request_template"):
#             field_prefix = "request_template__"
#         else:
#             field_prefix = ""

#         for system in systems:
#             q_filter = q_filter | Q(
#                 **{
#                     f"{field_prefix}system": system.name,
#                     f"{field_prefix}system_version": system.version,
#                     f"{field_prefix}namespace": system.namespace,
#                 }
#             )
#     else:
#         q_filter = Q()

#     return q_filter


# def _get_user_filter(model: Type[Document], user: "User") -> Q:
#     username_attr = _model_username_field_map.get(model.__name__)

#     if username_attr:
#         q_filter = Q(**{username_attr: user.username})
#     else:
#         q_filter = Q()

#     return q_filter


# def _get_garden_name_field(model: Type[Document]):
#     """Returns the name of the model field that corresponds to garden name"""
#     field_name_map = {
#         "Garden": "name",
#         "Job": "request_template__namespace",
#     }

#     return field_name_map.get(model.__name__, "namespace")


# def _get_object_ids_from_domain(domain: RoleAssignmentDomain) -> list:
#     """Retrieve the object ids (as strings) that correspond to the given domain"""
#     model = getattr(beer_garden.db.mongo.models, domain.scope)
#     model_objects = model.objects.filter(**domain.identifiers)

#     return [str(object_id) for object_id in model_objects.values_list("id")]


# def _get_garden_id_from_namespace(obj):
#     """Returns the Garden id corresponding to the supplied object based on the namespace
#     field from the object or its request_template
#     """
#     obj_with_namespace = getattr(obj, "request_template", None) or obj
#     namespace = getattr(obj_with_namespace, "namespace", None)

#     if namespace:
#         try:
#             garden_id = Garden.objects.get(name=namespace).id
#         except DoesNotExist:
#             garden_id = None
#     else:
#         garden_id = None

#     return garden_id


# def _get_system_id_from_request(obj):
#     """Returns the System id corresponding to the supplied object based on the fields
#     representing a system on the object or its request_template (i.e system, version,
#     and namespace)
#     """
#     obj_with_system = getattr(obj, "request_template", None) or obj

#     try:
#         system_id = System.objects.get(
#             name=obj_with_system.system,
#             version=obj_with_system.system_version,
#             namespace=obj_with_system.namespace,
#         ).id
#     except DoesNotExist:
#         system_id = None

#     return system_id


# def _get_object_garden_id(obj):
#     """Finds the Garden id (as a string) for the supplied object"""
#     garden_id = None

#     if isinstance(obj, Garden):
#         garden_id = obj.id
#     elif isinstance(obj, BrewtilsGarden):
#         garden_id = ObjectIdField().to_mongo(obj.id)
#     else:
#         garden_id = _get_garden_id_from_namespace(obj)

#     return str(garden_id) if garden_id else None


# def _get_object_system_id(obj) -> Optional[str]:
#     """Finds the System id (as a string) for the supplied object"""
#     system_id = None

#     if isinstance(obj, System):
#         system_id = obj.id
#     elif isinstance(obj, BrewtilsSystem):
#         system_id = ObjectIdField().to_python(obj.id)
#     elif type(obj) in _types_that_derive_system_from_request:
#         system_id = _get_system_id_from_request(obj)

#     return str(system_id) if system_id else None


# def _user_has_object_owner_permission(
#     user: "User", permission: str, obj: Union[Document, BrewtilsModel]
# ) -> bool:
#     """Determine if the user should have implicit access to the supplied object because
#     they are the object's owner"""
#     obj_type_name = type(obj).__name__
#     username_attr = _model_username_field_map.get(obj_type_name)

#     if username_attr:
#         return (permission in OBJECT_OWNER_PERMISSIONS) and (
#             user.username == getattr(obj, username_attr)
#         )
#     else:
#         return False
