from enum import Enum

from brewtils.errors import ModelValidationError, RoutingRequestException
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
import brewtils.models
from typing import Union
import beer_garden
import requests
import json


class Route_Type(Enum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4


class Routable_Garden_Name(Enum):
    PARENT = 1
    CHILD = 2


Routing_Eligible = Union[
    brewtils.models.Instance.schema,
    brewtils.models.Request.schema,
    brewtils.models.RequestTemplate.schema,
    brewtils.models.System.schema,
    brewtils.models.Event.schema,
]


def _local_garden():
    return beer_garden.config.get("garden.name")


def route_request(brewtils_obj=None, brewtils_model: str = None, obj_id: str = None, garden_name: str = None,
                  src_garden_name: str = None, route_type: Route_Type = None, **kwargs):
    # Rules for Routing:
    # 1: Model Type must be approved for routing
    # 2: Routing can only go Parent to Child
    #   2.1: If Source is child, treat as an update
    #   2.2: Parents will receive events through the Events Manager
    # 3: By Default, Source of request will be assumed local
    # 4: By Default, Routing Type will be assumed to be a READ
    # 5: Required Combination for Routing Request
    #   5.1: obj_id + brewtils_model
    #   5.2: brewtils_obj w/ schema populated
    #   5.3: brewtils_obj + brewtils_model
    # 6. All UPDATE requests must use PATCH for the brewtils_obj

    if route_type is None:
        route_type = Route_Type.READ

    if src_garden_name is None:
        src_garden_name = _local_garden()

    if brewtils_model is None and brewtils_obj and brewtils_obj.schema:
        brewtils_model = brewtils_obj.schema

    if brewtils_model is None:
        raise RoutingRequestException("Unable to identify Model Schema")

    elif brewtils_model is brewtils.models.PatchOperation.schema and obj_id is None:
        raise RoutingRequestException("Unable to route Patch Request, no Obj id provided")

    if brewtils_model in Routing_Eligible and src_garden_name is not Routable_Garden_Name.Child:

        if garden_name is None:
            if route_type in [Route_Type.DELETE, Route_Type.UPDATE]:

                # For objects that are requested to be deleted, we need to first collect
                # the object to determine if it should be routed.
                if obj_id is None:
                    raise RoutingRequestException(
                        "Unable to lookup %s for Route delete because ID was not provided" % brewtils_model)

                elif brewtils_model == brewtils.models.Instance.schema:
                    request_object = beer_garden.instances.get_instance(obj_id)
                    system = beer_garden.systems.get_system(instances__contains=request_object)
                    garden_name = system.garden_name

                elif brewtils_model == brewtils.models.Request.schema:
                    request_object = beer_garden.requests.get_request(obj_id)
                    system = beer_garden.systems.get_system(name_space=request_object.name_space,
                                                            name=request_object.system,
                                                            version=request_object.version)
                    garden_name = system.garden_name

                elif brewtils_model == brewtils.models.System.schema:
                    request_object = beer_garden.systems.get_system(obj_id)
                    garden_name = request_object.garden_name

            elif route_type is Route_Type.CREATE:
                request_object = SchemaParser.parse(brewtils_obj, brewtils_model, from_string=False)

                if brewtils_model == brewtils.models.Request.schema:
                    system = beer_garden.systems.get_system(name_space=request_object.name_space,
                                                            name=request_object.system,
                                                            version=request_object.version)
                    garden_name = system.garden_name

                elif brewtils_model == brewtils.models.System.schema:
                    garden_name = request_object.garden_name

        if garden_name is not src_garden_name:
            return forward_routing(garden_name=garden_name,
                                   brewtils_obj=brewtils_obj,
                                   brewtils_model=brewtils_model,
                                   obj_id=obj_id,
                                   src_garden_name=Routable_Garden_Name.PARENT,
                                   route_type=route_type,
                                   **kwargs)

    # Local routing is pushed down to the model classes.
    # That way developers updating the class don't forget about routing

    if brewtils_model is brewtils.models.Command.schema:
        beer_garden.commands.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model is brewtils.models.Instance.schema:
        beer_garden.instances.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model is brewtils.models.Job.schema:
        beer_garden.scheduler.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model in [brewtils.models.Request.schema, brewtils.models.RequestTemplate.schema]:
        beer_garden.requests.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model is brewtils.models.System.schema:
        beer_garden.systems.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model is brewtils.models.Garden.schema:
        beer_garden.garden.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model is 'LOGGING':
        beer_garden.log.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    elif brewtils_model is 'QUEUE':
        beer_garden.queues.route_request(brewtils_obj=brewtils_obj, obj_id=obj_id, route_type=route_type, **kwargs)

    else:
        raise RoutingRequestException("No route for %s exist" % brewtils_model)


def forward_routing(brewtils_obj=None, brewtils_model: str = None, obj_id: str = None, garden_name: str = None,
                    src_garden_name: str = None, route_type: Route_Type = None, **kwargs):
    garden_routing = beer_garden.garden.get_garden(garden_name)
    if garden_routing.connection_type in ['HTTP', 'HTTPS']:
        return forward_routing_http(garden_routing, brewtils_obj=brewtils_obj, brewtils_model=brewtils_model,
                                    obj_id=obj_id,
                                    src_garden_name=src_garden_name, route_type=route_type, **kwargs)
    else:
        raise RoutingRequestException("No forwarding route for %s exist" % garden_routing.connection_type)


def forward_routing_http(garden_routing, brewtils_obj=None, brewtils_model: str = None, obj_id: str = None,
                         src_garden_name: str = None, route_type: Route_Type = None, **kwargs):
    connection = garden_routing.connection_params
    endpoint = "{}://{}:{}{}api/v1/forward".format(
        "https" if connection['ssl'] else "http",
        connection['public_fqdn'],
        connection['port'],
        connection['url_prefix'],
    )

    headers = {
        "brewtils_model": brewtils_model,
        "obj_id": obj_id,
        "src_garden_name": src_garden_name,
        "route_type": route_type,
        "extra_kwargs": json.dump(kwargs)
    }

    if connection['ssl']:
        # @TODO Find a better place to get the SSL config info to children forwarding
        http_config = beer_garden.config.get("entry.http")
        response = requests.post(endpoint, headers=headers, data=brewtils_obj, cert=http_config.ssl.ca_cert,
                                 verify=http_config.ssl.ca_path)
    else:
        response = requests.post(endpoint, headers=headers, data=brewtils_obj)

    return response.content
