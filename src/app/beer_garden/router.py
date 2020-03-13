# -*- coding: utf-8 -*-
import logging
from typing import Dict, Tuple

import requests
from brewtils.models import Events, Garden, Instance, Operation, Request, System
from brewtils.schema_parser import SchemaParser

import beer_garden
import beer_garden.commands
import beer_garden.config as config
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
from beer_garden.garden import get_gardens
from beer_garden.systems import get_systems

logger = logging.getLogger(__name__)

# These are the operations that we will forward to child gardens
routable_operations = ["INSTANCE_START", "INSTANCE_STOP", "REQUEST_CREATE"]

# Processor that will be used for forwarding
forward_processor = None

# Dict of str(system) -> garden_name for determining which garden to use
garden_lookup: Dict[str, str] = {}

# Dict of garden_name -> (conn_type, conn_info) to be used for actual communication
garden_connections: Dict[str, Tuple[str, dict]] = {}

route_functions = {
    "REQUEST_CREATE": beer_garden.requests.process_request,
    "REQUEST_START": beer_garden.requests.start_request,
    "REQUEST_COMPLETE": beer_garden.requests.complete_request,
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
    logger.debug(f"Routing {operation}")

    operation = _pre_route(operation)

    if not operation.operation_type:
        raise RoutingRequestException(
            f"Unknown operation type '{operation.operation_type}'"
        )

    # Then use that to determine which garden the operation is targeting
    operation.target_garden_name = _determine_target_garden(operation)

    # If it's targeted at THIS garden, execute
    if operation.target_garden_name == config.get("garden.name"):
        return execute_local(operation)

    # Otherwise, validate that it can be forwarded
    if operation.operation_type not in routable_operations:
        raise RoutingRequestException(
            f"Operation type '{operation.operation_type}' can not be forwarded"
        )

    # TODO - Potentially check to ensure conn_info is not 'local' before forwarding

    return initiate_forward(operation)


def execute_local(operation: Operation):
    """Execute an operation on the local garden

    Args:
        operation:

    Returns:

    """
    operation = _pre_execute(operation)

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
    try:
        conn_type, conn_info = garden_connections[operation.target_garden_name]
    except KeyError:
        raise UnknownGardenException(
            f"Unknown child garden {operation.target_garden_name}"
        )

    try:
        if conn_type.casefold() == "http":
            return _forward_http(operation, conn_info)
        else:
            raise RoutingRequestException(f"Unknown connection type {conn_type}")
    except Exception as ex:
        logger.exception(f"Error publishing to forward{ex}")


def setup_routing():
    """Initialize the routing subsystem

    This will load the cached child garden definitions and use them to populate the
    two dictionaries that matter, garden_lookup and garden_connections.

    It will then query the database for all local systems and add those to the
    dictionaries as well.
    """
    local_garden_name = config.get("garden.name")

    # We do NOT want to load local garden information from the database as the local
    # name could have changed
    for garden in get_gardens():
        if garden.name != local_garden_name:
            if (
                garden.connection_type is not None
                and garden.connection_type.casefold() != "local"
            ):
                # add_garden(garden)

                # Mark all systems as reachable by this garden
                for system_name in garden.systems:
                    garden_lookup[system_name] = garden.name

                # Add to the connection lookup
                garden_connections[garden.name] = (
                    garden.connection_type,
                    garden.connection_params,
                )
            else:
                logger.warning(f"Adding garden with invalid connection info: {garden}")

    # Now add the local systems
    local_systems = get_systems(filter_params={"local": True})

    for system in local_systems:
        garden_lookup[str(system)] = local_garden_name

    logger.debug("Routing setup complete")


# def add_garden(garden: Garden):
#     # Mark all systems as reachable by this garden
#     for system_name in garden.systems:
#         garden_lookup[system_name] = garden.name
#
#     # Add to the connection lookup
#     garden_connections[garden.name] = (garden.connection_type, garden.connection_params)


def remove_garden(garden: Garden):
    # Remove all systems with this garden
    for system_name, garden_name in garden_lookup.items():
        if garden.name == garden_name:
            del garden_lookup[system_name]

    # Remove from the garden connection lookup
    del garden_connections[garden.name]


def handle_event(event):
    """Handle events

    Intended to be a callback invoked because of a downstream SYSTEM_CREATED event.
    """
    if event.name in (Events.SYSTEM_CREATED.name, Events.SYSTEM_UPDATED.name):
        garden_lookup[str(event.payload)] = event.garden

    if event.garden != config.get("garden.name"):
        if event.name == Events.GARDEN_STARTED.name:

            # Mark all systems as reachable by this garden
            for system_name in event.payload.systems:
                garden_lookup[system_name] = event.payload.name

        elif event.name == Events.GARDEN_REMOVED.name:
            remove_garden(event.payload)


def _pre_route(operation: Operation) -> Operation:
    """Called before any routing logic is applied"""
    # If no source garden is defined set it to the local garden
    if operation.source_garden_name is None:
        operation.source_garden_name = config.get("garden.name")

    return operation


def _pre_forward(operation: Operation) -> Operation:
    """Called before forwarding an operation"""
    if operation.operation_type == "REQUEST_CREATE":
        operation.model = beer_garden.requests.RequestValidator.instance().validate_request(
            operation.model
        )

        # Save the request so it'll have an ID and we'll have something to update
        operation.model = db.create(operation.model)

        # Clear parent before forwarding so the child doesn't freak out about an
        # unknown request
        operation.model.parent = None
        operation.model.has_parent = False

    return operation


def _pre_execute(operation: Operation) -> Operation:
    """Called before executing an operation"""
    # If there's a model present, shove it in the front
    if operation.model:
        operation.args.insert(0, operation.model)

    return operation


def _determine_target_garden(operation: Operation) -> str:
    """Determine the system the operation is targeting"""

    # Certain operations are ASSUMED to be targeted at the local garden
    if (
        "READ" in operation.operation_type
        or "GARDEN" in operation.operation_type
        or "JOB" in operation.operation_type
        or operation.operation_type in ("LOG_RELOAD", "SYSTEM_CREATE", "SYSTEM_RESCAN")
    ):
        return config.get("garden.name")

    # Otherwise, each operation needs to be "parsed"
    target_system = None

    if operation.operation_type in ("SYSTEM_DELETE", "SYSTEM_RELOAD", "SYSTEM_UPDATE"):
        target_system = db.query_unique(System, id=operation.args[0])

    elif "INSTANCE" in operation.operation_type:
        target_instance = db.query_unique(Instance, id=operation.args[0])
        target_system = db.query_unique(System, instances__contains=target_instance)

    elif operation.operation_type == "REQUEST_CREATE":
        target_system = System(
            namespace=operation.model.namespace,
            name=operation.model.system,
            version=operation.model.system_version,
        )

    elif operation.operation_type.startswith("REQUEST"):
        request = db.query_unique(Request, id=operation.args[0])

        target_system = System(
            namespace=request.namespace,
            name=request.system,
            version=request.system_version,
        )

    elif operation.operation_type == "QUEUE_DELETE":
        # Need to deconstruct the queue name
        parts = operation.args[0].split(".")
        version = parts[2].replace("-", ".")

        target_system = System(namespace=parts[0], name=parts[1], version=version)

    try:
        return garden_lookup[str(target_system)]
    except KeyError:
        raise UnknownGardenException(f"Unknown target garden for {operation}")


def _forward_http(operation: Operation, conn_info: dict):
    """Actually forward an operation using HTTP

    Args:
        operation: The operation to forward
        conn_info: Connection info
    """
    endpoint = "{}://{}:{}{}api/v1/forward".format(
        "https" if conn_info.get("ssl") else "http",
        conn_info.get("public_fqdn"),
        conn_info.get("port"),
        conn_info.get("url_prefix", "/"),
    )

    if conn_info.get("ssl"):
        http_config = config.get("entry.http")
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
