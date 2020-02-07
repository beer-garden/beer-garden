import json
from enum import Enum

import brewtils.models
import requests
from brewtils.errors import ModelValidationError

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


class Route_Type(Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


def enum_lookup(enum, value):
    for record in enum:
        if record.value == value:
            return record
    return None


class Route_Class(Enum):
    COMMAND = brewtils.models.Command.schema
    INSTANCE = brewtils.models.Instance.schema
    JOB = brewtils.models.Job.schema
    REQUEST = brewtils.models.Request.schema
    REQUEST_TEMPLATE = brewtils.models.RequestTemplate.schema
    SYSTEM = brewtils.models.System.schema
    GARDEN = brewtils.models.Garden.schema
    EVENT = brewtils.models.Event.schema
    LOGGING = brewtils.models.LoggingConfig.schema
    QUEUE = brewtils.models.Queue.schema


class Routable_Garden_Name(Enum):
    PARENT = 1
    CHILD = 2


Routing_Eligible = [
    Route_Class.INSTANCE,
    Route_Class.REQUEST,
    Route_Class.REQUEST_TEMPLATE,
    Route_Class.SYSTEM,
    Route_Class.EVENT,
]


def _local_garden():
    return beer_garden.config.get("garden.name")


System_Garden_Mapping = dict()
Garden_Connections = dict()


def get_garden_connection(garden_name):
    connection = Garden_Connections.get(garden_name, None)
    if connection is None:
        connection = beer_garden.garden.get_garden(garden_name)
        Garden_Connections[garden_name] = connection

    return connection


def update_garden_connection(connection):
    Garden_Connections[connection.garden_name] = connection


def remove_garden_connection(connection):
    Garden_Connections.pop(connection.garden_name, None)


def get_system_mapping(system=None, name_space=None, version=None, name=None):
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
    System_Garden_Mapping[str(system)] = garden_name


def remove_system_mapping(system):
    System_Garden_Mapping.pop(str(system), None)


def route_request(
    brewtils_obj=None,
    route_class: str = None,
    obj_id: str = None,
    garden_name: str = None,
    src_garden_name: str = None,
    route_type: Route_Type = None,
    **kwargs,
):
    # Rules for Routing:
    # 1: Model Type must be approved for routing
    # 2: Routing can only go Parent to Child
    #   2.1: If Source is child, treat as an update
    #   2.2: Parents will receive events through the Events Manager
    # 3: By Default, Source of request will be assumed local
    # 4: By Default, Routing Type will be assumed to be a READ
    # 5: Required Combination for Routing Request
    #   5.1: obj_id + route_class
    #   5.2: brewtils_obj w/ schema populated
    #   5.3: brewtils_obj + route_class
    # 6. All UPDATE requests must use PATCH for the brewtils_obj

    if route_type is None:
        route_type = Route_Type.READ

    if src_garden_name is None:
        src_garden_name = _local_garden()

    if route_class is None and brewtils_obj and brewtils_obj.schema:
        route_class = enum_lookup(Route_Class, brewtils_obj.schema)

    if route_class is None:
        raise RoutingRequestException("Unable to identify route")

    if (
        route_class in Routing_Eligible
        and src_garden_name is not Routable_Garden_Name.CHILD
    ):

        if garden_name is None:
            if route_type in [Route_Type.DELETE, Route_Type.UPDATE]:

                # For objects that are requested to be deleted, we need to first collect
                # the object to determine if it should be routed.
                if obj_id is None:
                    raise RoutingRequestException(
                        "Unable to lookup %s for Route delete because ID was not provided"
                        % route_class
                    )

                elif route_class == Route_Class.INSTANCE:
                    request_object = beer_garden.instances.get_instance(obj_id)
                    systems = beer_garden.systems.get_systems(
                        instances__contains=request_object
                    )
                    if len(systems) == 1:
                        garden_name = System_Garden_Mapping.get(str(systems[0]), None)

                elif route_class == Route_Class.SYSTEM:
                    system = beer_garden.systems.get_system(obj_id)
                    garden_name = System_Garden_Mapping.get(str(system), None)

            elif route_type is Route_Type.CREATE:
                if route_class in [Route_Class.REQUEST, Route_Class.REQUEST_TEMPLATE]:
                    garden_name = get_system_mapping(
                        name_space=brewtils_obj.namespace,
                        system=brewtils_obj.system,
                        version=brewtils_obj.system_version,
                    )

        if garden_name is not src_garden_name and garden_name is not None:
            return forward_routing(
                garden_name=garden_name,
                brewtils_obj=brewtils_obj,
                route_class=route_class,
                obj_id=obj_id,
                src_garden_name=Routable_Garden_Name.PARENT,
                route_type=route_type,
                **kwargs,
            )

    if route_class == Route_Class.COMMAND:
        if route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.commands.get_command(obj_id)
            else:
                return beer_garden.commands.get_commands()

    elif route_class == Route_Class.INSTANCE:

        if route_type == Route_Type.UPDATE:
            if route_type is Route_Type.UPDATE:
                for op in brewtils_obj:
                    operation = op.operation.lower()

                    if operation == "initialize":
                        runner_id = None
                        if op.value:
                            runner_id = op.value.get("runner_id")

                        return beer_garden.plugin.initialize(
                            obj_id, runner_id=runner_id
                        )

                    elif operation == "start":
                        return beer_garden.plugin.start(obj_id)

                    elif operation == "stop":
                        return beer_garden.plugin.stop(obj_id)

                    elif operation == "heartbeat":
                        return beer_garden.plugin.update(obj_id, new_status="RUNNING")

                    elif operation == "replace":
                        if op.path.lower() == "/status":
                            return beer_garden.plugin.update(
                                obj_id, new_status=op.value
                            )
                        else:
                            raise ModelValidationError(f"Unsupported path '{op.path}'")

                    elif operation == "update":
                        if op.path.lower() == "/metadata":
                            return beer_garden.plugin.update(obj_id, metadata=op.value)
                        else:
                            raise ModelValidationError(f"Unsupported path '{op.path}'")
                    else:
                        raise ModelValidationError(
                            f"Unsupported operation '{op.operation}'"
                        )

                return beer_garden.plugin.update(obj_id, brewtils_obj)
        else:
            if route_type is Route_Type.READ:
                return beer_garden.instances.get_instance(obj_id)
            elif route_type is Route_Type.DELETE:
                return beer_garden.instances.remove_instance(obj_id)

    elif route_class == Route_Class.JOB:

        if route_type is Route_Type.CREATE:
            return beer_garden.scheduler.create_job(brewtils_obj)
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.scheduler.get_job(obj_id)
            else:
                return beer_garden.scheduler.get_jobs(**kwargs)

        elif route_type is Route_Type.UPDATE:
            for op in brewtils_obj:
                if op.operation == "update":
                    if op.path == "/status":
                        if str(op.value).upper() == "PAUSED":
                            return beer_garden.scheduler.pause_job(obj_id)
                        elif str(op.value).upper() == "RUNNING":
                            return beer_garden.scheduler.resume_job(obj_id)
                        else:
                            raise ModelValidationError(
                                f"Unsupported status value '{op.value}'"
                            )
                    else:
                        raise ModelValidationError(
                            f"Unsupported path value '{op.path}'"
                        )
                else:
                    raise ModelValidationError(
                        f"Unsupported operation '{op.operation}'"
                    )

        elif route_type is Route_Type.DELETE:
            return beer_garden.scheduler.remove_job(obj_id)

    elif route_class in [Route_Class.REQUEST, Route_Class.REQUEST_TEMPLATE]:
        if route_type is Route_Type.CREATE:
            return beer_garden.requests.process_request(brewtils_obj, **kwargs)
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.requests.get_request(obj_id)
            else:
                return beer_garden.requests.get_requests(**kwargs)
        elif route_type is Route_Type.UPDATE:
            return beer_garden.requests.update_request(obj_id, brewtils_obj)

    elif route_class == Route_Class.SYSTEM:

        if route_type is Route_Type.CREATE:
            return beer_garden.systems.create_system(brewtils_obj)
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.systems.get_system(obj_id)
            else:
                return beer_garden.systems.get_systems(**kwargs)
        elif route_type is Route_Type.UPDATE:
            if obj_id:
                return beer_garden.systems.update_system(obj_id, brewtils_obj)
            else:
                return beer_garden.systems.update_rescan(brewtils_obj)
        elif route_type is Route_Type.DELETE:
            return beer_garden.systems.remove_system(obj_id)

    elif route_class == Route_Class.GARDEN:

        if route_type is Route_Type.CREATE:
            return beer_garden.garden.create_garden(brewtils_obj)
        elif route_type is Route_Type.READ:
            return beer_garden.garden.get_garden(obj_id)
        elif route_type is Route_Type.UPDATE:
            return beer_garden.garden.update_garden(obj_id, brewtils_obj)
        elif route_type is Route_Type.DELETE:
            return beer_garden.garden.remove_garden(obj_id)

    elif route_class == Route_Class.LOGGING:
        if route_type is Route_Type.READ:
            return beer_garden.log.get_plugin_log_config(obj_id)
        elif route_type is Route_Type.UPDATE:
            for op in brewtils_obj:
                if op.operation == "reload":
                    return beer_garden.log.reload_plugin_log_config()
                else:
                    raise ModelValidationError(
                        f"Unsupported operation '{op.operation}'"
                    )

    elif route_class == Route_Class.QUEUE:

        if route_type is Route_Type.READ:
            return beer_garden.queues.get_all_queue_info()
        elif route_type is Route_Type.DELETE:
            if obj_id:
                return beer_garden.queues.clear_queue(obj_id)
            else:
                return beer_garden.queues.clear_all_queues()

    raise RoutingRequestException(
        f"{route_type.value} route for {route_class} does not exist"
    )


def forward_routing(
    brewtils_obj=None,
    route_class: str = None,
    obj_id: str = None,
    garden_name: str = None,
    src_garden_name: str = None,
    route_type: Route_Type = None,
    **kwargs,
):
    garden_routing = Garden_Connections.get(garden_name, None)
    if garden_routing and garden_routing.connection_type in ["HTTP", "HTTPS"]:
        return forward_routing_http(
            garden_routing,
            brewtils_obj=brewtils_obj,
            route_class=route_class,
            obj_id=obj_id,
            src_garden_name=src_garden_name,
            route_type=route_type,
            **kwargs,
        )
    else:
        raise RoutingRequestException(
            "No forwarding route for %s exist" % garden_routing.connection_type
        )


def forward_routing_http(
    garden_routing,
    brewtils_obj=None,
    route_class: str = None,
    obj_id: str = None,
    src_garden_name: str = None,
    route_type: Route_Type = None,
    **kwargs,
):
    connection = garden_routing.connection_params
    endpoint = "{}://{}:{}{}api/v1/forward".format(
        "https" if connection["ssl"] else "http",
        connection["public_fqdn"],
        connection["port"],
        connection["url_prefix"],
    )

    headers = {
        "route_class": route_class,
        "obj_id": obj_id,
        "src_garden_name": src_garden_name,
        "route_type": route_type,
        "extra_kwargs": json.dump(kwargs),
    }

    if connection["ssl"]:
        # @TODO Find a better place to get the SSL config info to children forwarding
        http_config = beer_garden.config.get("entry.http")
        response = requests.post(
            endpoint,
            headers=headers,
            data=brewtils_obj,
            cert=http_config.ssl.ca_cert,
            verify=http_config.ssl.ca_path,
        )
    else:
        response = requests.post(endpoint, headers=headers, data=brewtils_obj)

    return response.content
