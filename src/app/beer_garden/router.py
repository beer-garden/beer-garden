from enum import Enum
from functools import partial
import requests

import brewtils.models

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
from beer_garden.errors import RoutingRequestException
from brewtils.schema_parser import SchemaParser


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


def forward_elgible(operation: brewtils.models.Operation):
    """
    Routing logic to determine if a request should be forwarded

    Args:
        operation:

    Returns:

    """
    return (
            operation.source_garden_name is not None
            and operation.target_garden_name is not None
            and operation.source_garden_name is not Routable_Garden_Name.CHILD.name
            and operation.target_garden_name is not operation.source_garden_name
            and operation.target_garden_name is not _local_garden()
    )


def forward_elgible_request(operation: brewtils.models.Operation):
    """
    Preps Request object forwards prior to evaluation

    Args:
        forward:

    Returns:

    """
    if operation.target_garden_name is None:
        for arg in operation.args:
            if isinstance(arg, (brewtils.models.Request, brewtils.models.RequestTemplate)):
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
                    operation.target_garden_name = get_system_mapping(system=bg_systems[0])

            elif isinstance(arg, brewtils.models.Instance):
                bg_systems = beer_garden.systems.get_systems(instances__contains=arg)
                if len(bg_systems) == 1:
                    operation.target_garden_name = get_system_mapping(system=bg_systems[0])

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


class Route_Class(Enum):
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
    INSTANCE_DELETE = (
        beer_garden.instances.remove_instance,
        forward_elgible_instance,
    )
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

    def __init__(self, function, forward_eligible):
        self.function = function
        self.forward_eligible = forward_eligible

    def execute(self, operation):
        if operation.source_garden_name is None:
            operation.source_garden_name = _local_garden()
        if self.forward_eligible and self.forward_eligible(operation):
            return forward_routing(operation)
        # Todo: Figure out why this doesn't work
        # return partial(self.module, self.function, *forward.args, **forward.kwargs)

        return partial(self.value[0], *operation.args, **operation.kwargs)()


System_Garden_Mapping = dict()
Garden_Connections = dict()


def get_garden_connection(garden_name):
    """
    Reaches into the database to get the garden connection information

    Args:
        garden_name:

    Returns:

    """
    connection = Garden_Connections.get(garden_name, None)
    if connection is None:
        connection = beer_garden.garden.get_garden(garden_name)
        Garden_Connections[garden_name] = connection
        pass

    return connection


def update_garden_connection(connection):
    """
    Caches the Garden Connection Information

    Args:
        connection:

    Returns:

    """
    Garden_Connections[connection.garden_name] = connection


def remove_garden_connection(connection):
    """
    Removes garden from the cache

    Args:
        connection:

    Returns:

    """
    Garden_Connections.pop(connection.garden_name, None)


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


def route_request(operation):
    """
    Runs the execute method of the Route Class Type

    Args:
        operation:

    Returns:

    """
    route_class = enum_lookup(Route_Class, operation.forward_type)
    return route_class.execute(operation)


def forward_routing(operation: brewtils.models.Operation):
    """
    Preps the Operation Object to be forwarded to child. If it is not configured, then it
    will raise an error.

    Args:
        operation:
    """
    operation.source_garden_name = Routable_Garden_Name.PARENT.name

    garden_routing = Garden_Connections.get(operation.target_graden_name, None)
    if garden_routing and garden_routing.connection_type in ["HTTP", "HTTPS"]:
        return forward_routing_http(operation)
    else:
        raise RoutingRequestException(
            "No forwarding route for %s exist" % garden_routing.connection_type
        )


def forward_routing_http(garden_routing, operation):
    """
    Invokes the HTTP Forwarding Logic

    :param garden_routing:
    :param operation:
    :return:
    """
    connection = garden_routing.connection_params

    endpoint = "{}://{}:{}{}api/v1/forward".format(
        "https" if connection["ssl"] else "http",
        connection["public_fqdn"],
        connection["port"],
        connection["url_prefix"],
    )

    if connection["ssl"]:
        http_config = beer_garden.config.get("entry.http")
        return requests.post(
            endpoint,
            data=SchemaParser.serialize_operation(operation),
            cert=http_config.ssl.ca_cert,
            verify=http_config.ssl.ca_path)

    else:
        return requests.post(
            endpoint,
            data=SchemaParser.serialize_operation(operation))
