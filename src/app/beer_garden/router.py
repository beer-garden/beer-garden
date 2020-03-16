from typing import Dict, List

import requests
from brewtils.models import Garden, Instance, Operation, System
from brewtils.schema_parser import SchemaParser

import beer_garden
import beer_garden.commands
import beer_garden.db.api as db
import beer_garden.garden
import beer_garden.instances
import beer_garden.log
import beer_garden.namespace
import beer_garden.plugin
import beer_garden.queues
import beer_garden.requests
import beer_garden.scheduler
import beer_garden.systems
from beer_garden.errors import RoutingRequestException, UnknownGardenException

# These are the operations that we will forward to child gardens
routable_operations = [
    "INSTANCE_START",
    "INSTANCE_STOP",
    "REQUEST_CREATE",
    "SYSTEM_DELETE",
]

# Processor that will be used for forwarding
forward_processor = None

# Dict that will be used to determine which garden to use
garden_map: Dict[str, Garden] = {}

# List of known gardens
gardens: List[Garden] = []

route_functions = {
    "REQUEST_CREATE": beer_garden.requests.process_request,
    "REQUEST_UPDATE": beer_garden.requests.update_request,
    "REQUEST_READ": beer_garden.requests.get_request,
    "REQUEST_READ_ALL": beer_garden.requests.get_requests,
    "COMMAND_READ": beer_garden.commands.get_command,
    "COMMAND_READ_ALL": beer_garden.commands.get_commands,
    "INSTANCE_READ": beer_garden.instances.get_instance,
    "INSTANCE_DELETE": beer_garden.instances.remove_instance,
    "INSTANCE_UPDATE": beer_garden.plugin.update,
    "INSTANCE_INITIALIZE": beer_garden.plugin.initialize,
    "INSTANCE_START": beer_garden.plugin.start,
    "INSTANCE_STOP": beer_garden.plugin.stop,
    "JOB_CREATE": beer_garden.scheduler.create_job,
    "JOB_READ": beer_garden.scheduler.get_job,
    "JOB_READ_ALL": beer_garden.scheduler.get_jobs,
    "JOB_PAUSE": beer_garden.scheduler.pause_job,
    "JOB_RESUME": beer_garden.scheduler.resume_job,
    "JOB_DELETE": beer_garden.scheduler.remove_job,
    "SYSTEM_CREATE": beer_garden.systems.create_system,
    "SYSTEM_READ": beer_garden.systems.get_system,
    "SYSTEM_READ_ALL": beer_garden.systems.get_systems,
    "SYSTEM_UPDATE": beer_garden.systems.update_system,
    "SYSTEM_RESCAN": beer_garden.systems.rescan_system_directory,
    "SYSTEM_DELETE": beer_garden.systems.purge_system,
    "GARDEN_CREATE": beer_garden.garden.create_garden,
    "GARDEN_READ": beer_garden.garden.get_garden,
    "GARDEN_READ_ALL": beer_garden.garden.get_gardens,
    "GARDEN_UPDATE_STATUS": beer_garden.garden.update_garden_status,
    "GARDEN_UPDATE_CONFIG": beer_garden.garden.update_garden_config,
    "GARDEN_DELETE": beer_garden.garden.remove_garden,
    "LOG_READ": beer_garden.log.get_plugin_log_config,
    "LOG_RELOAD": beer_garden.log.reload_plugin_log_config,
    "QUEUE_READ": beer_garden.queues.get_all_queue_info,
    "QUEUE_DELETE": beer_garden.queues.clear_queue,
    "QUEUE_DELETE_ALL": beer_garden.queues.clear_all_queues,
    "NAMESPACE_READ_ALL": beer_garden.namespace.get_namespaces,
}


def route(operation: Operation):
    """Entry point into the routing subsystem

    Args:
        operation: The operation to route

    Returns:

    """
    operation = _pre_route(operation)

    if should_forward(operation):
        return initiate_forward(operation)

    return execute_local(operation)


def should_forward(operation: Operation) -> bool:
    """Routing logic to determine if an operation should be forwardedl

    Args:
        operation:

    Returns:
        True if the operation should be forwarded, False if it should be executed
    """
    return (
        operation.target_garden_name is not None
        and operation.target_garden_name != operation.source_garden_name
        and operation.target_garden_name != _local_garden()
        and operation.operation_type in routable_operations
    )


def execute_local(operation: Operation):
    """Execute an operation on the local garden

    Args:
        operation:

    Returns:

    """
    _pre_execute(operation)

    return route_functions[operation.operation_type](
        *operation.args, **operation.kwargs
    )


def initiate_forward(operation: Operation):
    """Forward an operation to a child garden

    Will:
    - Pre-process the operation
    - Put the operation on the queue for forwarding
    - Return the "correct" response based on operation type

    Args:
        operation:
    """
    operation = _pre_forward(operation)

    forward_processor.put(operation)

    if operation.operation_type == "REQUEST_CREATE":
        return operation.model


def forward(operation: Operation):
    """Forward the operation to a child garden

    Intended to be called in the context of an executor or processor.

    Args:
        operation: The operation to forward

    Returns:
        The result of the specific forward transport function used

    Raises:
        RoutingRequestException: Could not determine a route to child
        UnknownGardenException: The specified target garden is unknown
    """
    target_garden = None
    for garden in gardens:
        if garden.name == operation.target_garden_name:
            target_garden = garden
            break

    if not target_garden:
        raise UnknownGardenException(
            f"Unknown child garden {operation.target_garden_name}"
        )

    if target_garden.connection_type is None:
        target_garden = beer_garden.garden.get_garden(target_garden.name)
        cache_gardens()

    if target_garden.connection_type and target_garden.connection_type.casefold() in [
        "http",
        "https",
    ]:
        return _forward_http(operation, target_garden)
    else:
        raise RoutingRequestException(
            f"Unknown connection type {target_garden.connection_type}"
        )


def cache_gardens():
    for garden in beer_garden.garden.get_gardens():
        add_garden(garden)


def add_garden(garden: Garden):
    # Mark all systems as reachable by this garden
    for system_name in garden.systems:
        garden_map[system_name] = garden

    # Add to the garden listing
    gardens.append(garden)


def remove_garden(garden: Garden):
    # Remove all systems with this garden
    for system_name, target_garden in garden_map.values():
        if target_garden == garden:
            del garden_map[system_name]

    # Remove from the garden listing
    gardens.remove(garden)


def _pre_route(operation: Operation):
    """

    Args:
        operation:

    Returns:

    """
    # If no source garden is defined set it to the local garden
    if operation.source_garden_name is None:
        operation.source_garden_name = _local_garden()

    # If no target is specified see if one can be determined
    if operation.target_garden_name is None:
        if operation.operation_type == "REQUEST_CREATE":
            target_system = System(
                namespace=operation.model.namespace,
                name=operation.model.system,
                version=operation.model.system_version,
            )
            target_garden = _determine_garden(system=target_system)

            operation.target_garden_name = target_garden.name

        elif operation.operation_type in ("INSTANCE_START", "INSTANCE_STOP"):
            target_instance = db.query_unique(Instance, id=operation.args[0])
            target_system = db.query_unique(System, instances__contains=target_instance)
            target_garden = _determine_garden(system=target_system)

            operation.target_garden_name = target_garden.name
        elif operation.operation_type in ("SYSTEM_DELETE",):
            target_system = db.query_unique(System, id=operation.args[0])
            target_garden = _determine_garden(system=target_system)

            operation.target_garden_name = target_garden.name

    return operation


def _pre_forward(operation: Operation):
    """Called before forwarding an operation"""
    if operation.operation_type == "REQUEST_CREATE":
        operation.model = db.create(operation.model)
        operation.model.parent = None
        operation.model.has_parent = False

    return operation


def _pre_execute(operation: Operation):
    """Called before executing an operation locally"""
    # If there's a model present, shove it in the front
    args = operation.args
    if operation.model:
        args.insert(0, operation.model)


def _forward_http(operation: Operation, garden: Garden):
    """Actually forward an operation using HTTP

    Args:
        operation: The operation to forward
        garden: The Garden to forward to
    """
    connection = garden.connection_params

    endpoint = "{}://{}:{}{}api/v1/forward".format(
        "https" if connection.get("ssl") else "http",
        connection.get("host"),
        connection.get("port"),
        connection.get("url_prefix", "/"),
    )

    if connection.get("ssl"):
        http_config = beer_garden.config.get("entry.http")
        return requests.post(
            endpoint,
            data=SchemaParser.serialize_operation(operation),
            cert=http_config.ssl.ca_cert,
            verify=http_config.ssl.ca_path,
        )

    else:
        return requests.post(
            endpoint,
            data=SchemaParser.serialize_operation(operation),
            headers={"Content-type": "application/json", "Accept": "text/plain"},
        )


def _local_garden():
    """Get the local garden name"""
    return beer_garden.config.get("garden.name")


def _determine_garden(system):
    """Retrieve a garden from the garden map

    Args:
        system:

    Returns:

    """
    garden = garden_map.get(str(system))
    if garden is None:

        # If you can't find it, force a cache to make sure everything is updated
        cache_gardens()
        garden = garden_map.get(str(system))
        if garden is None:
            raise ValueError("Unable to determine target garden")

    return garden
