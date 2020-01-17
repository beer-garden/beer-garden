from enum import Enum

from brewtils.errors import ModelValidationError
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
import brewtils.models
from typing import Union
import beer_garden


class Route_Type(Enum):
    CREATE = 1
    READ = 2
    UPDATE = 3
    DELETE = 4


class Routable_Garden_Name(Enum):
    PARENT = 1
    CHILD = 2


Routing_Eligible = Union[
    brewtils.models.Instance,
    brewtils.models.Request,
    brewtils.models.RequestTemplate,
    brewtils.models.System,
    brewtils.models.Event,
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

    if route_type is None:
        route_type = Route_Type.READ

    if src_garden_name is None:
        src_garden_name = _local_garden()

    if brewtils_model is None and brewtils_obj and brewtils_obj.schema:
        brewtils_model = brewtils_obj.schema

    if brewtils_model is None:
        raise ModelValidationError("Unable to identify Model Schema")

    if brewtils_model is brewtils.models.PatchOperation.schema and obj_id is None:
        raise ModelValidationError("Unable to route Patch Request, no Obj id provided")

    elif brewtils_obj:
        request_object = SchemaParser.parse(brewtils_obj, brewtils_model, from_string=False)

    if brewtils_model in Routing_Eligible and src_garden_name is not Routable_Garden_Name.Child:

        if garden_name is None:
            if route_type == Route_Type.DELETE:

                # For objects that are requested to be deleted, we need to first collect
                # the object to determine if it should be routed.
                if obj_id is None:
                    raise Exception("Unable to lookup %s for Route delete because ID was not provided" % brewtils_model)

                elif brewtils_model == brewtils.models.Instance.schema:
                    request_object = beer_garden.instances.get_instance(obj_id)
                    garden_name = request_object.garden_name
                    system = beer_garden.systems.get_system(instances__contains=request_object)

                elif brewtils_model == brewtils.models.Request.schema:
                    request_object = beer_garden.requests.get_request(obj_id)
                    system = beer_garden.systems.get_system(name_space=request_object.name_space,
                                                            name=request_object.system,
                                                            version=request_object.version)

                elif brewtils_model == brewtils.models.System.schema:
                    request_object = beer_garden.systems.get_system(obj_id)

            # Only they System Object contains the Garden Name that allows routing
            if brewtils_model == brewtils.models.Instance.schema:
                system = beer_garden.systems.get_system(instances__contains=request_object)
                garden_name = system.garden_name

            elif brewtils_model == brewtils.models.Request.schema:
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

    # now write spaghetti code for all of the services

    if brewtils_model is brewtils.models.Command.schema:
        if route_type is Route_Type.CREATE:
            pass
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.commands.get_command(obj_id)
            else:
                return beer_garden.commands.get_commands()
        elif route_type is Route_Type.UPDATE:
            pass
        elif route_type is Route_Type.DELETE:
            pass

    elif brewtils_model is brewtils.models.Instance.schema:
        if route_type is Route_Type.CREATE:
            pass
        elif route_type is Route_Type.READ:
            return beer_garden.instances.get_instance(obj_id)
        elif route_type is Route_Type.UPDATE:
            return beer_garden.instances.update_instance(obj_id, brewtils_obj)
        elif route_type is Route_Type.DELETE:
            return beer_garden.instances.remove_instance(obj_id)

    elif brewtils_model is brewtils.models.Job.schema:
        if route_type is Route_Type.CREATE:
            return beer_garden.scheduler.create_job(brewtils_obj)
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.scheduler.get_job(obj_id)
            else:
                return beer_garden.scheduler.get_jobs(kwargs.get('filter_params', None))
        elif route_type is Route_Type.UPDATE:
            # Does not exist yet
            # return beer_garden.scheduler.update_job(obj_id, brewtils_obj)
            pass
        elif route_type is Route_Type.DELETE:
            return beer_garden.scheduler.remove_job(obj_id)

    elif brewtils_model in [brewtils.models.Request.schema, brewtils.models.RequestTemplate.schema]:
        if route_type is Route_Type.CREATE:
            return beer_garden.requests.process_request(
                                            request_object,
                                            wait_timeout=kwargs.get('wait_timeout', -1))
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.requests.get_request(obj_id)
            else:
                return beer_garden.requests.get_requests(kwargs.get('serialize_kwargs', None))
        elif route_type is Route_Type.UPDATE:
            return beer_garden.requests.update_request(obj_id, brewtils_obj)
        elif route_type is Route_Type.DELETE:
            pass

    elif brewtils_model is brewtils.models.System.schema:
        if route_type is Route_Type.CREATE:
            return beer_garden.systems.create_system(brewtils_obj)
        elif route_type is Route_Type.READ:
            if obj_id:
                return beer_garden.systems.get_system(obj_id)
            else:
                return beer_garden.systems.get_systems(
                    serialize_kwargs=kwargs.get('serialize_kwargs', None),
                    filter_params=kwargs.get('filter_params', None),
                    order_by=kwargs.get('order_by', None),
                    include_fields=kwargs.get('include_fields', None),
                    exclude_fields=kwargs.get('exclude_fields', None),
                    dereference_nested=kwargs.get('dereference_nested', None), )
        elif route_type is Route_Type.UPDATE:
            return beer_garden.systems.update_system(obj_id, brewtils_obj)
        elif route_type is Route_Type.DELETE:
            return beer_garden.systems.remove_system(obj_id)

    elif brewtils_model is brewtils.models.Garden.schema:
        if route_type is Route_Type.CREATE:
            return beer_garden.garden.create_garden(brewtils_obj)
        elif route_type is Route_Type.READ:
            return beer_garden.garden.get_garden(obj_id)
        elif route_type is Route_Type.UPDATE:
            return beer_garden.garden.update_garden(obj_id, brewtils_obj)
        elif route_type is Route_Type.DELETE:
            return beer_garden.garden.remove_garden(obj_id)

    elif brewtils_model is 'LOGGING':
        if route_type is Route_Type.CREATE:
            pass
        elif route_type is Route_Type.READ:
            return beer_garden.log.get_plugin_log_config(obj_id)
        elif route_type is Route_Type.UPDATE:
            # Does not exist
            # return beer_garden.log.update_plugin_log_config(brewtils_obj)
            pass
        elif route_type is Route_Type.DELETE:
            pass

    elif brewtils_model is 'QUEUE':
        if route_type is Route_Type.CREATE:
            pass
        elif route_type is Route_Type.READ:
            return beer_garden.queues.get_all_queue_info()
        elif route_type is Route_Type.UPDATE:
            pass
        elif route_type is Route_Type.DELETE:
            if obj_id:
                return beer_garden.queues.clear_queue(obj_id)
            else:
                return beer_garden.queues.clear_all_queues()
