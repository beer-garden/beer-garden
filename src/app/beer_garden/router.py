from enum import Enum
from typing import Dict

import brewtils.models
import requests
from brewtils.models import Garden, Operation
from brewtils.schema_parser import SchemaParser

import beer_garden
import beer_garden.commands
import beer_garden.garden
import beer_garden.instances
import beer_garden.log
import beer_garden.plugin
import beer_garden.queues
import beer_garden.requests
import beer_garden.scheduler
import beer_garden.systems
from beer_garden.errors import RoutingRequestException, UnknownGardenException

# These are the operations that we can forward to child gardens
routable_operations = ["REQUEST_CREATE"]

System_Garden_Mapping = {}
child_connections: Dict[str, Garden] = {
    "child": Garden(
        garden_name="child",
        connection_type="HTTP",
        connection_params={"public_fqdn": "localhost", "port": 2338},
    )
}


def route(operation: Operation):
    """Entry point into the routing subsystem

    Args:
        operation:

    Returns:

    """
    # If no source garden is defined set it to the local garden
    if operation.source_garden_name is None:
        operation.source_garden_name = _local_garden()

    if should_forward(operation):
        return forward(operation)

    return execute_local(operation)


def should_forward(operation: brewtils.models.Operation) -> bool:
    """Routing logic to determine if a request should be forwarded

    Args:
        operation:

    Returns:
        True if the operation should be forwarded, False if it should be executed
    """
    return (
        operation.target_garden_name is not None
        and operation.source_garden_name != Routable_Garden_Name.CHILD.name
        and operation.target_garden_name != operation.source_garden_name
        and operation.target_garden_name != _local_garden()
    )


def execute_local(operation: Operation):
    """Execute an operation on the local garden

    Args:
        operation:

    Returns:

    """
    # If there's a model present, shove it in the front
    args = operation.args
    if operation.model:
        args.insert(0, operation.model)

    # Get the function to execute from the enum list
    route_class = enum_lookup(RouteClass, operation.operation_type)

    return route_class.value[0](*operation.args, **operation.kwargs)


def forward(operation: Operation):
    """Forward an operation to a child garden

    Args:
        operation:

    Raises:
        RoutingRequestException: Could not determine a route to child
        UnknownGardenException: The specified target garden is unknown
    """
    # operation.source_garden_name = Routable_Garden_Name.PARENT.name

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


def _local_garden():
    """
    Gets local garden name

    Returns:

    """
    return beer_garden.config.get("garden.name")


def enum_lookup(enum, name):
    """
    Quick lookup function to find ENUM value

    Args:
        enum:
        name:

    Returns:

    """
    for record in enum:
        if record.name == name:
            return record
    return None


class Routable_Garden_Name(Enum):
    PARENT = 1
    CHILD = 2


def forward_elgible_request(operation: Operation):
    """
    Preps Request object forwards prior to evaluation

    Args:
        operation:

    Returns:

    """
    if operation.target_garden_name is None:
        for arg in operation.args:
            if isinstance(
                arg, (brewtils.models.Request, brewtils.models.RequestTemplate)
            ):
                operation.target_garden_name = get_system_mapping(
                    name_space=arg.namespace,
                    system=arg.system,
                    version=arg.system_version,
                )
    return forward_elgible(operation)


def forward_elgible_instance(operation: brewtils.models.Operation):
    """
    Preps Instance object forwards prior to evaluation

    Args:
        operation:

    Returns:

    """
    if operation.target_garden_name is None:
        for arg in operation.args:

            if isinstance(arg, str):
                instance = beer_garden.instances.get_instance(arg)
                bg_systems = beer_garden.systems.get_systems(
                    instances__contains=instance
                )
                if len(bg_systems) == 1:
                    operation.target_garden_name = get_system_mapping(
                        system=bg_systems[0]
                    )

            elif isinstance(arg, brewtils.models.Instance):
                bg_systems = beer_garden.systems.get_systems(instances__contains=arg)
                if len(bg_systems) == 1:
                    operation.target_garden_name = get_system_mapping(
                        system=bg_systems[0]
                    )

    return forward_elgible(operation)


def forward_elgible_system(operation: brewtils.models.Operation):
    """
    Preps System object operations prior to evaluation

    Args:
        operation:

    Returns:

    """
    if operation.target_garden_name is None:
        for arg in operation.args:

            if isinstance(arg, str):
                system = beer_garden.systems.get_system(arg)
                operation.target_garden_name = get_system_mapping(system=system)

            elif isinstance(arg, brewtils.models.System):
                operation.target_garden_name = get_system_mapping(system=arg)

    return forward_elgible(operation)


class RouteClass(Enum):
    # How to create new Route Class
    # ARG 1 = Target Function
    # ARG 2 = Routing Eligibility Check

    REQUEST_CREATE = (beer_garden.requests.process_request, forward_elgible_request)
    REQUEST_UPDATE = (beer_garden.requests.update_request, None)
    REQUEST_READ = (beer_garden.requests.get_request, None)
    REQUEST_READ_ALL = (beer_garden.requests.get_requests, None)

    COMMAND_READ = (beer_garden.commands.get_command, None)
    COMMAND_READ_ALL = (beer_garden.commands.get_commands, None)

    INSTANCE_READ = (beer_garden.instances.get_instance, None)
    INSTANCE_DELETE = (beer_garden.instances.remove_instance, forward_elgible_instance)
    INSTANCE_UPDATE = (beer_garden.plugin.update, forward_elgible_instance)
    INSTANCE_INITIALIZE = (beer_garden.plugin.initialize, None)
    INSTANCE_START = (beer_garden.plugin.start, None)
    INSTANCE_STOP = (beer_garden.plugin.stop, None)

    JOB_CREATE = (beer_garden.scheduler.create_job, None)
    JOB_READ = (beer_garden.scheduler.get_job, None)
    JOB_READ_ALL = (beer_garden.scheduler.get_jobs, None)
    JOB_PAUSE = (beer_garden.scheduler.pause_job, None)
    JOB_RESUME = (beer_garden.scheduler.resume_job, None)
    JOB_DELETE = (beer_garden.scheduler.remove_job, None)

    SYSTEM_CREATE = (beer_garden.systems.create_system, None)
    SYSTEM_READ = (beer_garden.systems.get_system, None)
    SYSTEM_READ_ALL = (beer_garden.systems.get_systems, None)
    SYSTEM_UPDATE = (beer_garden.systems.update_system, forward_elgible_system)
    SYSTEM_RESCAN = (beer_garden.systems.rescan_system_directory, None)
    SYSTEM_DELETE = (beer_garden.systems.remove_system, forward_elgible_system)

    GARDEN_CREATE = (beer_garden.garden.create_garden, None)
    GARDEN_READ = (beer_garden.garden.get_garden, None)
    GARDEN_UPDATE = (beer_garden.garden.update_garden, None)
    GARDEN_DELETE = (beer_garden.garden.remove_garden, None)

    LOG_READ = (beer_garden.log.get_plugin_log_config, None)
    LOG_RELOAD = (beer_garden.log.reload_plugin_log_config, None)

    QUEUE_READ = (beer_garden.queues.get_all_queue_info, None)
    QUEUE_DELETE = (beer_garden.queues.clear_queue, None)
    QUEUE_DELETE_ALL = (beer_garden.queues.clear_all_queues, None)


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


def update_garden_connection(connection):
    """
    Caches the Garden Connection Information

    Args:
        connection:

    Returns:

    """
    child_connections[connection.garden_name] = connection


def remove_garden_connection(connection):
    """
    Removes garden from the cache

    Args:
        connection:

    Returns:

    """
    child_connections.pop(connection.garden_name, None)


def get_system_mapping(system=None, name_space=None, version=None, name=None):
    """
    Gets the cached Garden mapping information, if it is not cached, it will add it to
    the cache

    Args:
        system:
        name_space:
        version:
        name:

    Returns:

    """
    if system:
        mapping = System_Garden_Mapping.get(str(system), None)
        if mapping is None:
            # @ TODO Integrate the garden mapping
            # mapping = beer_garden.system.get_garden_mapping(system.id)
            # System_Garden_Mapping[str(system)] = mapping
            pass
        return mapping
    else:
        system_str = "%s:%s-%s" % (name_space, name, version)
        mapping = System_Garden_Mapping.get(system_str, None)
        if mapping is None:
            systems = beer_garden.systems.get_systems(
                name_space=name_space, name=name, version=version
            )
            if len(systems) == 1:
                # @ TODO Integrate the garden mapping
                # mapping = beer_garden.system.get_garden_mapping(systems[0].id)
                # System_Garden_Mapping[system_str] = mapping
                pass
        return mapping


def update_system_mapping(system, garden_name):
    """
    Caches System to Garden information

    Args:
        system:
        garden_name:

    Returns:

    """
    System_Garden_Mapping[str(system)] = garden_name


def remove_system_mapping(system: brewtils.models.System):
    """
    Removes System mapping from cache

    Args:
        system:

    Returns:

    """
    System_Garden_Mapping.pop(str(system), None)


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
