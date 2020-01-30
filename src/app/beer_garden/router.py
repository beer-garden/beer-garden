from enum import Enum

from beer_garden.errors import RoutingRequestException
from brewtils.errors import ModelValidationError
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
import brewtils.models
from typing import Union
import beer_garden
import requests
import json


class Route_Type(Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class Route_Class(Enum):
    COMMAND = brewtils.models.Command.schema
    INSTANCE = brewtils.models.Instance.schema
    JOB = brewtils.models.Job.schema
    REQUEST = brewtils.models.Request.schema
    REQUEST_TEMPLATE = brewtils.models.RequestTemplate.schema
    SYSTEM = brewtils.models.System.schema
    GARDEN = brewtils.models.Garden.schema
    EVENT = brewtils.models.Event.schema
    LOGGING = "LOGGING"
    QUEUE = "QUEUE"


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


def route_request(
    brewtils_obj=None,
    route_class: str = None,
    obj_id: str = None,
    garden_name: str = None,
    src_garden_name: str = None,
    route_type: Route_Type = None,
    **kwargs
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
        route_class = brewtils_obj.schema

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
                    system = beer_garden.systems.get_system(
                        instances__contains=request_object
                    )
                    garden_name = system.garden_name

                elif route_class in [Route_Class.REQUEST, Route_Class.REQUEST_TEMPLATE]:
                    request_object = beer_garden.requests.get_request(obj_id)
                    system = beer_garden.systems.get_system(
                        name_space=request_object.name_space,
                        name=request_object.system,
                        version=request_object.version,
                    )
                    garden_name = system.garden_name

                elif route_class == Route_Class.SYSTEM:
                    request_object = beer_garden.systems.get_system(obj_id)
                    garden_name = request_object.garden_name

            elif route_type is Route_Type.CREATE:

                if route_class in [Route_Class.REQUEST, Route_Class.REQUEST_TEMPLATE]:
                    request_object = SchemaParser.parse_request(
                        brewtils_obj, from_string=False
                    )
                    system = beer_garden.systems.get_system(
                        name_space=request_object.name_space,
                        name=request_object.system,
                        version=request_object.version,
                    )
                    garden_name = system.garden_name

                elif route_class == Route_Class.SYSTEM:
                    request_object = SchemaParser.parse_system(
                        brewtils_obj, from_string=False
                    )
                    garden_name = request_object.garden_name

        if garden_name is not src_garden_name and garden_name is not None:
            return forward_routing(
                garden_name=garden_name,
                brewtils_obj=brewtils_obj,
                route_class=route_class,
                obj_id=obj_id,
                src_garden_name=Routable_Garden_Name.PARENT,
                route_type=route_type,
                **kwargs
            )

    # Local routing is pushed down to the model classes.
    # That way developers updating the class don't forget about routing

    if route_class == Route_Class.COMMAND:
        return beer_garden.commands.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    elif route_class == Route_Class.INSTANCE:
        if route_type == Route_Type.UPDATE:
            beer_garden.plugin.route_request(
                brewtils_obj=brewtils_obj,
                obj_id=obj_id,
                route_type=route_type,
                **kwargs
            )
        else:
            beer_garden.instances.route_request(
                brewtils_obj=brewtils_obj,
                obj_id=obj_id,
                route_type=route_type,
                **kwargs
            )

    elif route_class == Route_Class.JOB:
        return beer_garden.scheduler.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    elif route_class in [Route_Class.REQUEST, Route_Class.REQUEST_TEMPLATE]:
        return beer_garden.requests.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    elif route_class == Route_Class.SYSTEM:
        return beer_garden.systems.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    elif route_class == Route_Class.GARDEN:
        return beer_garden.garden.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    elif route_class == Route_Class.LOGGING:
        return beer_garden.log.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    elif route_class == Route_Class.QUEUE:
        return beer_garden.queues.route_request(
            brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs
        )

    else:
        raise RoutingRequestException("No route for %s exist" % route_class)


def forward_routing(
    brewtils_obj=None,
    route_class: str = None,
    obj_id: str = None,
    garden_name: str = None,
    src_garden_name: str = None,
    route_type: Route_Type = None,
    **kwargs
):
    garden_routing = beer_garden.garden.get_garden(garden_name)
    if garden_routing.connection_type in ["HTTP", "HTTPS"]:
        return forward_routing_http(
            garden_routing,
            brewtils_obj=brewtils_obj,
            route_class=route_class,
            obj_id=obj_id,
            src_garden_name=src_garden_name,
            route_type=route_type,
            **kwargs
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
    **kwargs
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
