from enum import Enum
from functools import partial

import brewtils.models
from brewtils import EasyClient

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


def _local_garden():
    return beer_garden.config.get("garden.name")


def enum_lookup(enum, value):
    for record in enum:
        if record.value == value:
            return record
    return None


class Routable_Garden_Name(Enum):
    PARENT = 1
    CHILD = 2


def forward_elgible(forward: brewtils.models.Forward):
    """
    Routing logic to determine if a request should be forwarded

    :param forward: Forward request object that needs to be evaluated
    :return: Booelan response on if the object should be forwarded
    """
    return (
        forward.source_garden_name is not None
        and forward.target_garden_name is not None
        and forward.source_garden_name is not Routable_Garden_Name.CHILD.name
        and forward.target_garden_name is not forward.source_garden_name
        and forward.target_garden_name is not _local_garden()
    )


def forward_elgible_request(forward: brewtils.models.Forward):
    """
    Preps Request object forwards prior to evaluation
    :param forward: Forward request object that needs to be evaluated
    :return: Boolean response on if the object should be forwarded
    """
    if forward.target_garden_name is None:
        for arg in forward.args:
            if arg.schema in [
                brewtils.models.Request.schema,
                brewtils.models.RequestTemplate.schema,
            ]:
                forward.target_garden_name = get_system_mapping(
                    name_space=arg.namespace,
                    system=arg.system,
                    version=arg.system_version,
                )
    return forward_elgible(forward)


def forward_elgible_instance(forward: brewtils.models.Forward):
    """
    Preps Instance object forwards prior to evaluation
    :param forward: Forward request object that needs to be evaluated
    :return: Boolean response on if the object should be forwarded
    """
    if forward.target_garden_name is None:
        for arg in forward.args:
            if arg.schema in [brewtils.models.Instance.schema]:
                bg_systems = beer_garden.systems.get_systems(instances__contains=arg)
                if len(bg_systems) == 1:
                    forward.target_garden_name = System_Garden_Mapping.get(
                        str(bg_systems[0]), None
                    )
            elif isinstance(arg, str):
                instance = beer_garden.instances.get_instance(arg)
                bg_systems = beer_garden.systems.get_systems(
                    instances__contains=instance
                )
                if len(bg_systems) == 1:
                    forward.target_garden_name = System_Garden_Mapping.get(
                        str(bg_systems[0]), None
                    )

    return forward_elgible(forward)


def forward_elgible_system(forward: brewtils.models.Forward):
    """
    Preps System object forwards prior to evaluation
    :param forward: Forward request object that needs to be evaluated
    :return: Boolean response on if the object should be forwarded
    """
    if forward.target_garden_name is None:
        for arg in forward.args:
            if arg.schema in [brewtils.models.System]:
                forward.target_garden_name = System_Garden_Mapping.get(str(arg, None))
            elif isinstance(arg, str):
                system = beer_garden.systems.get_system(arg)
                forward.target_garden_name = System_Garden_Mapping.get(
                    str(system, None)
                )

    return forward_elgible(forward)


def Route_Class(Enum):
    # How to create new Route Class
    # ARG 1 = Target Module
    # ARG 2 = Target Function
    # ARG 3 = Routing Eligibility Check

    REQUEST_CREATE = (beer_garden.requests, "process_request", forward_elgible_request)
    REQUEST_UPDATE = (beer_garden.requests, "update_request", None)
    REQUEST_READ = (beer_garden.requests, "get_request", None)
    REQUEST_READ_ALL = (beer_garden.requests, "get_requests", None)

    COMMAND_READ = (beer_garden.commands, "get_command", None)
    COMMAND_READ_ALL = (beer_garden.commands, "get_commands", None)

    INSTANCE_READ = (beer_garden.instances, "get_instance", None)
    INSTANCE_DELETE = (
        beer_garden.instances,
        "remove_instance",
        forward_elgible_instance,
    )
    INSTANCE_UPDATE = (beer_garden.plugin, "update", forward_elgible_instance)
    INSTANCE_INITIALIZE = (beer_garden.plugin, "initialize", None)
    INSTANCE_START = (beer_garden.plugin, "start", None)

    JOB_CREATE = (beer_garden.scheduler, "create_job", None)
    JOB_READ = (beer_garden.scheduler, "get_job", None)
    JOB_READ_ALL = (beer_garden.scheduler, "get_jobs", None)
    JOB_PAUSE = (beer_garden.scheduler, "pause_job", None)
    JOB_RESUME = (beer_garden.scheduler, "resume_job", None)
    JOB_DELETE = (beer_garden.scheduler, "remove_job", None)

    SYSTEM_CREATE = (beer_garden.systems, "create_system", None)
    SYSTEM_READ = (beer_garden.systems, "get_system", None)
    SYSTEM_READ_ALL = (beer_garden.systems, "get_systems", None)
    SYSTEM_UPDATE = (beer_garden.systems, "update_system", forward_elgible_system)
    SYSTEM_RESCAN = (beer_garden.systems, "rescan_system_directory", None)
    SYSTEM_DELETE = (beer_garden.systems, "remove_system", forward_elgible_system)

    GARDEN_CREATE = (beer_garden.garden, "create_garden", None)
    GARDEN_READ = (beer_garden.garden, "get_garden", None)
    GARDEN_UPDATE = (beer_garden.garden, "update_garden", None)
    GARDEN_DELETE = (beer_garden.garden, "remove_garden", None)

    LOG_READ = (beer_garden.log, "get_plugin_log_config", None)
    LOG_RELOAD = (beer_garden.log, "reload_plugin_log_config", None)

    QUEUE_READ = (beer_garden.queues, "get_all_queue_info", None)
    QUEUE_DELETE = (beer_garden.queues, "clear_queue", None)
    QUEUE_DELETE_ALL = (beer_garden.queues, "clear_all_queues", None)

    def __init__(self, module, function, forward_eligible):
        self.module = module
        self.function = function
        self.forward_eligible = forward_eligible

    def execute(self, forward):
        if forward.source_garden_name is None:
            forward.source_garden_name = _local_garden()
        if self.forward_eligible and self.forward_eligible(forward):
            return forward_routing(forward)
        return partial(self.module, self.function, *forward.args, **forward.kwargs)


System_Garden_Mapping = dict()
Garden_Connections = dict()


def get_garden_connection(garden_name):
    """
    Reaches into the database to get the garden connection information

    :param garden_name:
    :return:
    """
    connection = Garden_Connections.get(garden_name, None)
    if connection is None:
        connection = beer_garden.garden.get_garden(garden_name)
        Garden_Connections[garden_name] = connection

    return connection


def update_garden_connection(connection):
    """
    Caches the Garden Connection Information

    :param connection:
    :return:
    """
    Garden_Connections[connection.garden_name] = connection


def remove_garden_connection(connection):
    """
    Removes garden from the cache

    :param connection:
    :return:
    """
    Garden_Connections.pop(connection.garden_name, None)


def get_system_mapping(system=None, name_space=None, version=None, name=None):
    """
    Gets the cached Garden mapping information, if it is not cached, it will add it to
    the cache

    :param system:
    :param name_space:
    :param version:
    :param name:
    :return:
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

    :param system:
    :param garden_name:
    :return:
    """
    System_Garden_Mapping[str(system)] = garden_name


def remove_system_mapping(system):
    """
    Removes System mapping from cache

    :param system:
    :return:
    """
    System_Garden_Mapping.pop(str(system), None)


def route_request(forward_class):
    """
    Runs the execute method of the Route Class Type

    :param forward_class:
    :return:
    """
    route_class = enum_lookup(Route_Class, forward_class.forward_type)
    return route_class.execute(forward_class)


def forward_routing(forward: brewtils.models.Forward):
    """
    Preps the Forward Object to be forwarded to child. If it is not configured, then it
    will raise an error.

    :param forward:
    :return:
    """
    forward.source_garden_name = Routable_Garden_Name.PARENT.name

    garden_routing = Garden_Connections.get(forward.target_graden_name, None)
    if garden_routing and garden_routing.connection_type in ["HTTP", "HTTPS"]:
        return forward_routing_http(forward)
    else:
        raise RoutingRequestException(
            "No forwarding route for %s exist" % garden_routing.connection_type
        )


def forward_routing_http(garden_routing, forward):
    """
    Invokes the HTTP Forwarding Logic

    :param garden_routing:
    :param forward:
    :return:
    """
    connection = garden_routing.connection_params

    if connection["ssl"]:
        http_config = beer_garden.config.get("entry.http")
        ez_client = EasyClient(
            bg_host=connection["public_fqdn"],
            bg_port=connection["port"],
            bg_url_prefix=connection["url_prefix"],
            ssl_enabled=connection["ssl"],
            ca_cert=http_config.ssl.ca_cert,
            client_cert=http_config.ssl.ca_path,
        )
    else:
        ez_client = EasyClient(
            bg_host=connection["public_fqdn"],
            bg_port=connection["port"],
            bg_url_prefix=connection["url_prefix"],
            ssl_enabled=connection["ssl"],
        )

    return ez_client.post_forward(forward)
