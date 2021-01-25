import logging
from beer_garden.api.http.authorization import PermissionRequiredAccess
from brewtils.errors import RequestForbidden
from beer_garden.plugin import _from_kwargs
from beer_garden.requests import get_request
from beer_garden.scheduler import get_job
from beer_garden.systems import get_system
from brewtils.models import (
    Request,
    RequestTemplate,
    System,
    Instance,
    Queue,
    Job,
    Operation,
    Principal,
    Runner,
)

logger = logging.getLogger(__name__)


def request_namespace(obj: Request = None) -> str:
    """
    Find the namespace for Request Model
    Args:
        obj: Request

    Returns: Namespace

    """
    return obj.namespace


def request_template_namespace(obj: RequestTemplate = None) -> str:
    """
    Finds the namespace for Request Template Model
    Args:
        obj: Request Template

    Returns: Namespace

    """
    return obj.namespace


def system_namespace(obj: System = None) -> str:
    """
    Finds the namespace for System Model
    Args:
        obj: System

    Returns: Namespace

    """
    return obj.namespace


def instance_namespace(obj: Instance = None) -> str:
    """
    Finds the System associated with the Instance to find the Namespace
    Args:
        obj: Instance

    Returns: Namespace

    """
    system, _ = _from_kwargs(instance_id=obj.id)
    return system_namespace(system)


def queue_namespace(obj: Queue = None) -> str:
    """
    Finds the System associated with the Queue to find the Namespace
    Args:
        obj:

    Returns:

    """
    system = get_system(obj.system_id)
    return system_namespace(system)


def job_namespace(obj: Job = None) -> str:
    """
    Finds the Namespace associated with the Job's Request Template
    Args:
        obj: Job

    Returns: Namespace

    """
    return request_template_namespace(obj.request_template)


def runner_namespace(obj: Runner = None) -> str:
    """
    Finds the Namespace associated with the Runner
    Args:
        obj: Runner

    Returns: Namespace

    """

    if obj.instance_id:
        system, _ = _from_kwargs(instance_id=obj.instance_id)
        obj.kwargs["system"] = system
        return system_namespace(system)

    return None


def operation_namespace(obj: Operation = None) -> str:
    """
    Finds the namespace associated with an Operation that is attempting to modify a
    record, then includes that source object to the operation to reduce redundant calls
    Args:
        obj: Operation

    Returns: Namespace

    """
    if "READ" not in obj.operation_type:
        if "REQUEST" in obj.operation_type:
            request_id = None
            if len(obj.args) > 0:
                request_id = obj.args[0]
            elif "request_id" in obj.kwargs:
                request_id = obj.kwargs["request_id"]
            if request_id:
                request = get_request(request_id)
                obj.kwargs["request"] = request
                return request_namespace(request)
        elif "SYSTEM" in obj.operation_type:
            system_id = None
            if len(obj.args) > 0:
                system_id = obj.args[0]
            elif "system_id" in obj.kwargs:
                system_id = obj.kwargs["system_id"]
            if system_id:
                system = get_system(system_id)
                obj.kwargs["system"] = system
                return system_namespace(system)

        elif "INSTANCE" in obj.operation_type:
            instance_id = None
            if len(obj.args) > 0:
                instance_id = obj.args[0]
            elif "instance_id" in obj.kwargs:
                instance_id = obj.kwargs["instance_id"]
            if instance_id:
                system, _ = _from_kwargs(instance_id=instance_id)
                obj.kwargs["system"] = system
                return system_namespace(system)
        elif "JOB" in obj.operation_type:
            job_id = None
            if len(obj.args) > 0:
                job_id = obj.args[0]
            elif "job_id" in obj.kwargs:
                job_id = obj.kwargs["job_id"]
            if job_id:
                job = get_job(job_id)
                return job_namespace(job)

    return None


def operation_filtering(
    obj: Operation = None,
    raise_error: bool = True,
    current_user: Principal = None,
    required_permissions: list = list(),
):
    """
    Filters the Operation Model based on Model field
    Args:
        obj: Operation to Filter
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation
        required_permissions: Required permissions defined for API

    Returns:

    """

    if obj.model and filter_brewtils_model(
        obj=obj.model,
        current_user=current_user,
        required_permissions=required_permissions,
        raise_error=raise_error,
    ):
        return obj


def operation_db_filtering(obj: Operation = None, current_user: Principal = None):
    """
    Injects custom filtering to reduce return from DB calls

    Args:
        obj: Operation model to be modified
        current_user: Principal record associated with the Operation

    Returns:

    """
    if "REQUEST_COUNT" == obj.operation_type:
        if "namespace__in" not in obj.kwargs:
            obj.kwargs["namespace__in"] = list()
        for permission in current_user.permissions:
            obj.kwargs["namespace__in"].append(permission.namespace)


def event_filtering(
    obj=None,
    raise_error: bool = True,
    current_user: Principal = None,
    required_permissions: list = list(),
):
    """
    Filters the Event Model based on Payload field
    Args:
        obj: Event to Filter
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation
        required_permissions: Required permissions defined for API

    Returns:

    """
    if obj.payload and filter_brewtils_model(
        obj=obj.payload,
        current_user=current_user,
        required_permissions=required_permissions,
        raise_error=raise_error,
    ):
        return obj


# Mapping for the different models for easy management
obj_namespace_mapping = {
    "InstanceSchema": instance_namespace,
    "JobSchema": job_namespace,
    "QueueSchema": queue_namespace,
    "RequestSchema": request_namespace,
    "RequestTemplateSchema": request_template_namespace,
    "SystemSchema": system_namespace,
    "OperationSchema": operation_namespace,
    "RunnerSchema": runner_namespace,
}

obj_custom_filtering_mapping = {
    "EventSchema": event_filtering,
    "OperationSchema": operation_filtering,
}

obj_db_filtering = {
    "OperationSchema": operation_db_filtering,
}


def filter_brewtils_model(
    obj=None,
    raise_error: bool = True,
    current_user: Principal = None,
    required_permissions: list = list(),
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
            current_user=current_user, required_permissions=required_permissions
        ):
            return obj
        if raise_error:
            raise RequestForbidden("Action requires permissions")

        return None

    # First we check if we have an easy mapping to the namespace
    obj_namespace = None
    if obj.schema in obj_namespace_mapping.keys():
        obj_namespace = obj_namespace_mapping[obj.schema](obj)

    # If we find a namespace, we can run the filter at this point
    if obj_namespace:
        if namespace_check(
            obj_namespace,
            current_user=current_user,
            required_permissions=required_permissions,
        ):
            return obj
        if raise_error:
            raise RequestForbidden("Action requires permissions %s" % obj_namespace)

        return None

    # Second attempt, if we have custom filtering for the object, lets use that instead
    if obj.schema in obj_custom_filtering_mapping.keys():
        return obj_custom_filtering_mapping[obj.schema](
            obj=obj,
            raise_error=raise_error,
            current_user=current_user,
            required_permissions=required_permissions,
        )

    # We have no way to filter, we will return the obj for now and log an error
    logger.error(f"Unable to filter obj for schema type {obj.schema}")

    return obj


def model_filter(
    obj=None,
    raise_error: bool = True,
    current_user: Principal = None,
    required_permissions: list = list(),
):
    """
    Filters a Model
    Args:
        obj: Model to Filter
        raise_error: If an Exception should be raised if not matching
        current_user: Principal record associated with the Operation
        required_permissions: Required permissions defined for API

    Returns:

    """
    if not required_permissions or len(required_permissions) == 0:
        return obj

    if not current_user:
        raise RequestForbidden("Action requires the User to be logged in")

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
                required_permissions=required_permissions,
            )
            if obj_item:
                new_obj.append(obj_item)
        return new_obj

    return filter_brewtils_model(
        obj=obj,
        raise_error=raise_error,
        current_user=current_user,
        required_permissions=required_permissions,
    )


def model_db_filter(obj=None, current_user: Principal = None):
    """
    Injects custom DB logic into model to improve filtering
    Args:
        obj: Model to filter
        current_user: Principal record associated with the Model

    Returns:

    """

    # Impossible to add filters, so we return the object
    if not hasattr(obj, "schema"):
        return

    # Local access gets them Read to everything, so no filtering
    for permission in current_user.permissions:
        if permission.is_local:
            return

    if obj.schema in obj_db_filtering.keys():
        obj_db_filtering[obj.schema](obj=obj, current_user=current_user)


def namespace_check(
    namespace: str, current_user: Principal = None, required_permissions: list = list()
):
    """
    Compares the namespace provided with the Principals permissions and required permissions
    Args:
        namespace: Namespace associated with Model
        current_user: Principal record associated with the Model
        required_permissions: Required permission level for the Model

    Returns:

    """
    for permission in current_user.permissions:
        for required in required_permissions:
            if permission.access in PermissionRequiredAccess[required] and (
                permission.namespace == namespace or permission.is_local
            ):
                return True

    return False


def permission_check(
    current_user: Principal = None, required_permissions: list = list()
):
    """
    Compares the namespace provided with the Principals permissions and required permissions
    Args:
        namespace: Namespace associated with Model
        current_user: Principal record associated with the Model
        required_permissions: Required permission level for the Model

    Returns:

    """
    for permission in current_user.permissions:
        for required in required_permissions:
            if permission.access in PermissionRequiredAccess[required]:
                return True

    return False
