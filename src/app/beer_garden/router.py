from typing import Dict

import requests
from brewtils.models import Garden, Operation, System
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
routable_operations = ["INSTANCE_START", "INSTANCE_STOP", "REQUEST_CREATE"]

# Processor that will be used for forwarding
forward_processor = None

# Dict that will be used to determine which garden to use
garden_map: Dict[str, Garden] = {}
child_connections = {}


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
    "SYSTEM_DELETE": beer_garden.systems.remove_system,
    "GARDEN_CREATE": beer_garden.garden.create_garden,
    "GARDEN_READ": beer_garden.garden.get_garden,
    "GARDEN_READ_ALL": beer_garden.garden.get_gardens,
    "GARDEN_UPDATE": beer_garden.garden.update_garden,
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


def _pre_route(operation: Operation):
    """

    Args:
        operation:

    Returns:

    """
    # If no source garden is defined set it to the local garden
    if operation.source_garden_name is None:
        operation.source_garden_name = _local_garden()

    if operation.target_garden_name is None:
        if operation.operation_type == "REQUEST_CREATE":
            operation.target_garden_name = _garden_for_request(operation).name

    return operation


def _garden_for_request(operation: Operation):
    """Determine target garden for a REQUEST_CREATE

    Args:
        operation:

    Returns:

    """
    request = operation.model

    return get_system_mapping(
        namespace=request.namespace,
        system=request.system,
        version=request.system_version,
    )


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

    func = route_functions[operation.operation_type]
    return func(*operation.args, **operation.kwargs)


def initiate_forward(operation: Operation):
    """Forward an operation to a child garden

    Will:
    - Pre-process the operation
    - Put the operation on the queue for forwarding
    - Return the "correct" response based on operation type

    Args:
        operation:
    """
    _pre_forward(operation)

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
    target_garden = child_connections.get(operation.target_garden_name)

    if not target_garden:
        raise UnknownGardenException(
            f"Unknown child garden {operation.target_garden_name}"
        )

    if target_garden.connection_type in ["HTTP", "HTTPS"]:
        return _forward_http(operation, target_garden)
    else:
        raise RoutingRequestException(
            f"Unknown connection type {target_garden.connection_type}"
        )


def _pre_forward(operation: Operation):
    """Called before forwarding an operation"""
    if operation.operation_type == "REQUEST_CREATE":
        operation.model = db.create(operation.model)


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
        connection.get("public_fqdn"),
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


def get_garden_connection(garden_name):
    """
    Reaches into the database to get the garden connection information

    Args:
        garden_name:

    Returns:

    """
    connection = child_connections.get(garden_name, None)
    if connection is None:
        connection = beer_garden.garden.get_garden(garden_name)
        child_connections[garden_name] = connection
        pass

    return connection


def update_garden_connection(garden: Garden):
    """
    Caches the Garden Connection Information

    Args:
        garden:

    Returns:

    """
    child_connections[garden.name] = garden


def remove_garden_connection(garden: Garden):
    """
    Removes garden from the cache

    Args:
        garden:

    Returns:

    """
    child_connections.pop(garden.name, None)


def get_system_mapping(system=None, namespace=None, version=None, name=None):
    """Retrieve a garden from the garden map

    Args:
        system:
        namespace:
        version:
        name:

    Returns:

    """
    system = system or System(namespace=namespace, name=name, version=version)

    garden = garden_map.get(str(system))
    if garden is None:
        raise ValueError("NO GARDEN SUCKA")

    return garden


def update_system_mapping(system: System, garden: Garden):
    """Adds or updates a system in the garden map

    Args:
        system:
        garden:

    Returns:

    """
    garden_map[str(system)] = garden


def remove_system_mapping(system: System):
    """Removes a system from garden map

    Args:
        system:

    Returns:

    """
    try:
        garden_map.pop(str(system))
    except KeyError:
        raise ValueError("System not in garden map")
