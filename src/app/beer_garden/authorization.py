import logging
from typing import Union

from brewtils.models import BaseModel as BrewtilsModel
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Event as BrewtilsEvent
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import Job as BrewtilsJob
from brewtils.models import Permissions
from brewtils.models import Request as BrewtilsRequest
from brewtils.models import RequestTemplate as BrewtilsRequestTemplate
from brewtils.models import Role as BrewtilsRole
from brewtils.models import Runner as BrewtilsRunner
from brewtils.models import System as BrewtilsSystem
from brewtils.models import User as BrewtilsUser
from mongoengine import Q

import beer_garden.config as config
import beer_garden.db.api as db

logger = logging.getLogger(__name__)


def check_global_roles(
    user: BrewtilsUser,
    permission_level: str = None,
    permission_levels: list = None,
) -> bool:
    if permission_levels is None:
        permission_levels = generate_permission_levels(permission_level)

    for roles in [
        user.local_roles if user.local_roles else [],
        user.upstream_roles if user.upstream_roles else [],
    ]:
        if any(
            role.permission in permission_levels and _has_empty_scopes(role)
            for role in roles
        ):
            return True

        # Check is the user has Garden Admin for the current Garden
        if any(
            role.permission == Permissions.GARDEN_ADMIN.name
            and (
                len(role.scope_gardens) == 0
                or config.get("garden.name") in role.scope_gardens
            )
            for role in roles
        ):
            return True

    return False


def generate_permission_levels(permission_level: str) -> list:
    if permission_level == Permissions.READ_ONLY.name:
        return [
            Permissions.READ_ONLY.name,
            Permissions.OPERATOR.name,
            Permissions.PLUGIN_ADMIN.name,
            Permissions.GARDEN_ADMIN.name,
        ]

    if permission_level == Permissions.OPERATOR.name:
        return [
            Permissions.OPERATOR.name,
            Permissions.PLUGIN_ADMIN.name,
            Permissions.GARDEN_ADMIN.name,
        ]

    if permission_level == Permissions.PLUGIN_ADMIN.name:
        return [Permissions.PLUGIN_ADMIN.name, Permissions.GARDEN_ADMIN.name]

    if permission_level == Permissions.GARDEN_ADMIN.name:
        return [Permissions.GARDEN_ADMIN.name]

    return []


def _has_empty_scopes(
    role: BrewtilsRole,
    scopes: list = None,
):
    if scopes is None:
        scopes = [
            "scope_gardens",
            "scope_namespaces",
            "scope_systems",
            "scope_instances",
            "scope_versions",
            "scope_commands",
        ]

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
        for roles in [user.local_roles, user.upstream_roles]:
            for role in roles:
                if role.permission in permission_levels:
                    for garden_scope in role.scope_gardens:
                        garden_names.append(garden_scope)

        return Q(**{"name__in": garden_names})

    def _get_request_filter(self, user: BrewtilsUser, permission_levels: list) -> Q:
        if check_global_roles(user, permission_levels=permission_levels):
            return Q()

        filters = []

        for roles in [user.local_roles, user.upstream_roles]:
            for role in roles:
                if role.permission in permission_levels:
                    filter = {}
                    if len(role.scope_systems) > 0:
                        filter["system__in"] = role.scope_systems
                    if len(role.scope_instances) > 0:
                        filter["instance_name__in"] = role.scope_instances
                    if len(role.scope_versions) > 0:
                        filter["system_version__in"] = role.scope_versions
                    if len(role.scope_commands) > 0:
                        filter["command__in"] = role.scope_commands

                    if len(filter) > 0:
                        filters.append(Q(**filter))

        if len(filters) == 0:
            return Q()

        output = None

        for filter in filters:
            if output is None:
                output = filter
            else:
                output = output | filter

        output = output | Q(requester=user.username)
        return output

    def _get_job_filter(self, user: BrewtilsUser, permission_levels: list) -> Q:
        if check_global_roles(user, permission_levels=permission_levels):
            return Q()

        filters = []

        for roles in [user.local_roles, user.upstream_roles]:
            for role in roles:
                if role.permission in permission_levels:
                    filter = {}
                    if len(role.scope_systems) > 0:
                        filter["request_template__system__in"] = role.scope_systems
                    if len(role.scope_instances) > 0:
                        filter["request_template__instance_name__in"] = (
                            role.scope_instances
                        )
                    if len(role.scope_versions) > 0:
                        filter["request_template__system_version__in"] = (
                            role.scope_versions
                        )
                    if len(role.scope_commands) > 0:
                        filter["request_template__command__in"] = role.scope_commands

                    if len(filter) > 0:
                        filters.append(Q(**filter))

        if len(filters) == 0:
            return Q()

        output = None

        for filter in filters:
            if output is None:
                output = filter
            else:
                output = output | filter

        return output

    def _get_system_filter(self, user: BrewtilsUser, permission_levels: list) -> Q:
        if check_global_roles(user, permission_levels=permission_levels):
            return Q()

        filters = []

        for roles in [user.local_roles, user.upstream_roles]:
            for role in roles:
                if role.permission in permission_levels:
                    filter = {}
                    if len(role.scope_systems) > 0:
                        filter["name__in"] = role.scope_systems
                    if len(role.scope_instances) > 0:
                        filter["instances__name__in"] = role.scope_instances
                    if len(role.scope_versions) > 0:
                        filter["version__in"] = role.scope_versions
                    if len(role.scope_commands) > 0:
                        filter["commands__name__in"] = role.scope_commands

                    if len(filter) > 0:
                        filters.append(Q(**filter))

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

        for roles in [user.local_roles, user.upstream_roles]:
            for role in roles:
                if role.permission in permission_levels:
                    filter = {}
                    if len(role.scope_instances) > 0:
                        filter["name__in"] = role.scope_instances

                    if len(filter) > 0:
                        filters.append(Q(**filter))

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

        if len(user.local_roles) == 0 and len(user.upstream_roles) == 0:
            return None

        if model is None:
            return Q()

        if model is BrewtilsGarden:
            return self._get_garden_q_filter(user, permission_levels)
        if model is BrewtilsSystem:
            return self._get_system_filter(user, permission_levels)
        if model is BrewtilsInstance:
            return self._get_instance_filter(user, permission_levels)
        if model is BrewtilsRequest:
            return self._get_request_filter(user, permission_levels)
        if model is BrewtilsJob:
            return self._get_job_filter(user, permission_levels)

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
                        BrewtilsSystem,
                        name=system_name,
                        version=system_version,
                        namespace=system_namespace,
                        raise_missing=True,
                    )
                elif system_name:
                    system = db.query_unique(
                        BrewtilsSystem, name=system_name, raise_missing=True
                    )
                elif instance_id:
                    system = db.query_unique(
                        BrewtilsSystem, instances__id=instance_id, raise_missing=True
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
            if system and system.id and not system.local:
                gardens = db.query(BrewtilsGarden, filter_params={"systems": system})

                if gardens and len(gardens) == 1:
                    garden_name = gardens[0].name
                else:
                    # TODO: Add better Exception
                    raise Exception(
                        "Unable to find source garden for Authorization checks"
                    )
            else:
                config.get("garden.name")

        for roles in [user.local_roles, user.upstream_roles]:
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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
            return role

        # Can return the role information, if the user has the role
        for user_role in user.local_roles:
            if role.name == user_role.name:
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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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

    def _get_runner_filter(
        self,
        runner: BrewtilsRunner,
        user: BrewtilsUser,
        permission_levels: list,
        source_system: BrewtilsSystem = None,
        source_garden_name: str = None,
        source_system_namespace: str = None,
        source_system_name: str = None,
        source_system_version: str = None,
        source_system_instances: list = None,
        skip_global: bool = False,
        skip_system: bool = False,
        **kwargs
    ):
        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
            return runner

        if self._checks(
            user,
            permission_levels=permission_levels,
            system=source_system,
            garden_name=source_garden_name,
            system_namespace=source_system_namespace,
            system_name=source_system_name,
            system_version=source_system_version,
            system_instances=source_system_instances,
            check_garden=True,
            check_system=not skip_system,
            check_namespace=not skip_system,
            check_version=not skip_system,
            check_instances=True,
            instance_id=runner.instance_id,
            **kwargs,
        ):
            return runner

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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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
        for roles in [user.local_roles, user.upstream_roles]:
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
        for roles in [user.local_roles, user.upstream_roles]:
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
            system.commands = filtered_commands

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

        if not skip_global and check_global_roles(
            user, permission_levels=permission_levels
        ):
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
            for roles in [user.local_roles, user.upstream_roles]:
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

                garden.systems = new_systems

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
        permission_levels=None,
        **kwargs
    ) -> BrewtilsModel:
        if isinstance(obj, BrewtilsUser):
            del obj.password

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
        if isinstance(obj, BrewtilsCommand):
            return self._get_command_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, BrewtilsEvent):
            if obj.payload:
                payload_filtered = self.filter_object(
                    obj.payload, user, permission_levels=permission_levels, **kwargs
                )
                if payload_filtered:
                    obj.payload = payload_filtered
                else:
                    return None
        if isinstance(obj, BrewtilsRunner):
            return self._get_runner_filter(
                obj, user, permission_levels, skip_global=True, **kwargs
            )
        if isinstance(obj, str) or isinstance(obj, dict):
            # Source of String is unknown, so ensure that a role has the basic permissions
            for roles in [
                user.local_roles if user.local_roles else [],
                user.upstream_roles if user.upstream_roles else [],
            ]:
                if any(role.permission in permission_levels for role in roles):
                    return obj

            return None

        # If object is outside of the filters, check for permissions at a minimum
        if check_global_roles(user, permission_levels=permission_levels):
            return obj
