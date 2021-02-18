import logging
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
    Runner,
    Event,
)

logger = logging.getLogger(__name__)


def request_garden_namespace(obj: Request = None) -> str:
    """
    Find the namespace for Request Model
    Args:
        obj: Request

    Returns: Namespace

    """
    return obj.garden, obj.namespace


def request_template_garden_namespace(obj: RequestTemplate = None) -> str:
    """
    Finds the namespace for Request Template Model
    Args:
        obj: Request Template

    Returns: Namespace

    """
    return obj.garden, obj.namespace


def system_garden_namespace(obj: System = None) -> str:
    """
    Finds the namespace for System Model
    Args:
        obj: System

    Returns: Namespace

    """
    return obj.garden, obj.namespace


def instance_garden_namespace(obj: Instance = None) -> str:
    """
    Finds the System associated with the Instance to find the Namespace
    Args:
        obj: Instance

    Returns: Namespace

    """
    system, _ = _from_kwargs(instance_id=obj.id)
    return system_garden_namespace(system)


def queue_garden_namespace(obj: Queue = None) -> str:
    """
    Finds the System associated with the Queue to find the Namespace
    Args:
        obj:

    Returns:

    """
    system = get_system(obj.system_id)
    return system_garden_namespace(system)


def job_garden_namespace(obj: Job = None) -> str:
    """
    Finds the Namespace associated with the Job's Request Template
    Args:
        obj: Job

    Returns: Namespace

    """
    return request_template_garden_namespace(obj.request_template)


def runner_garden_namespace(obj: Runner = None) -> str:
    """
    Finds the Namespace associated with the Runner
    Args:
        obj: Runner

    Returns: Namespace

    """

    if obj.instance_id:
        system, _ = _from_kwargs(instance_id=obj.instance_id)
        obj.kwargs["system"] = system
        return system_garden_namespace(system)

    return None, None


def operation_garden_namespace(obj: Operation = None) -> str:
    """
    Finds the namespace associated with an Operation that is attempting to modify a
    record, then includes that source object to the operation to reduce redundant calls
    Args:
        obj: Operation

    Returns: Namespace

    """

    # Attempt to derive namespace from arguments passed
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
                return request_garden_namespace(request)
        elif "SYSTEM" in obj.operation_type:
            system_id = None
            if len(obj.args) > 0:
                arg = obj.args[0]

                if type(arg) == str:
                    system_id = arg
                elif type(arg) == System:
                    return system_garden_namespace(arg)
            elif "system_id" in obj.kwargs:
                system_id = obj.kwargs["system_id"]
            if system_id:
                system = get_system(system_id)
                obj.kwargs["system"] = system
                return system_garden_namespace(system)

        elif "INSTANCE" in obj.operation_type:
            instance_id = None
            if len(obj.args) > 0:
                instance_id = obj.args[0]
            elif "instance_id" in obj.kwargs:
                instance_id = obj.kwargs["instance_id"]
            if instance_id:
                system, _ = _from_kwargs(instance_id=instance_id)
                obj.kwargs["system"] = system
                return system_garden_namespace(system)
        elif "JOB" in obj.operation_type:
            job_id = None
            if len(obj.args) > 0:
                job_id = obj.args[0]
            elif "job_id" in obj.kwargs:
                job_id = obj.kwargs["job_id"]
            if job_id:
                job = get_job(job_id)
                return job_garden_namespace(job)

    # Attempt to derive namespace from Model field
    if obj.model:
        return find_obj_garden_namespace(obj.model)

    return None, None


def event_garden_namespace(obj: Event = None) -> str:
    """
    Finds the namespace associated with an event
    Args:
        obj: Event

    Returns: Namespace

    """

    if obj.payload:
        return find_obj_garden_namespace(obj.payload)
    return None, None


# Mapping for the different models for easy management
obj_namespace_mapping = {
    "InstanceSchema": instance_garden_namespace,
    "JobSchema": job_garden_namespace,
    "QueueSchema": queue_garden_namespace,
    "RequestSchema": request_garden_namespace,
    "RequestTemplateSchema": request_template_garden_namespace,
    "SystemSchema": system_garden_namespace,
    "OperationSchema": operation_garden_namespace,
    "RunnerSchema": runner_garden_namespace,
    "EventSchema": event_garden_namespace,
}


def find_obj_garden_namespace(obj):
    if hasattr(obj, "schema") and obj.schema in obj_namespace_mapping.keys():
        return obj_namespace_mapping[obj.schema](obj)

    return None, None
