import logging
from time import sleep
from typing import List, Sequence

from brewtils.errors import ModelValidationError
from brewtils.models import Events, Instance, System, PatchOperation
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import SystemSchema

import beer_garden
from beer_garden.db.mongo.api import delete, query, query_unique, create, reload, update
from beer_garden.events import publish_event
from beer_garden.rabbitmq import get_routing_key

REQUEST_FIELDS = set(SystemSchema.get_attribute_names())

logger = logging.getLogger(__name__)


def get_system(system_id: str) -> System:
    """Retrieve an individual System

    Args:
        system_id: The System ID

    Returns:
        The System

    """
    return query_unique(System, id=system_id)


def get_systems(
    # filter_params: Dict[str, str] = None,
    # order_by: str = "name",
    # include_fields: Sequence[str] = None,
    # exclude_fields: Sequence[str] = None,
    # dereference_nested: bool = True,
    **kwargs
) -> List[System]:
    """Search for Systems

    It's possible to specify `include_fields` _and_ `exclude_fields`. This doesn't make
    a lot of sense, but you can do it. If the same field is in both `exclude_fields`
    takes priority (the field will NOT be included in the response).

    Args:
        filter_params: Dict of filtering parameters
        order_by: System attribute that will be used to order the result list
        include_fields: Fields to include for matching Systems
        exclude_fields: Fields to exclude for matching Systems
        dereference_nested: Flag specifying if Commands and Instances should be fetched

    Returns:
        The list of Systems that matched the query

    """
    return query(System, **kwargs)
    # query_set = System.objects.order_by(order_by)
    #
    # if include_fields:
    #     query_set = query_set.only(*include_fields)
    #
    # if exclude_fields:
    #     query_set = query_set.exclude(*exclude_fields)
    #
    # if not dereference_nested:
    #     query_set = query_set.no_dereference()
    #
    # filtered = query_set.filter(**(filter_params or {}))
    #
    # return SchemaParser.parse_system(
    #     MongoParser.serialize_system(filtered, to_string=False, many=True),
    #     from_string=False,
    #     many=True,
    # )


@publish_event(Events.SYSTEM_CREATED)
def create_system(system: System) -> System:
    """Create a new System

    Args:
        system: The System to create

    Returns:
        The created System

    """
    # Assign a default 'main' instance if there aren't any instances and there can
    # only be one
    if not system.instances or len(system.instances) == 0:
        if system.max_instances is None or system.max_instances == 1:
            system.instances = [Instance(name="default")]
            system.max_instances = 1
        else:
            raise ModelValidationError(
                f"Could not create system {system.name}-{system.version}: Systems with "
                f"max_instances > 1 must also define their instances"
            )
    else:
        if not system.max_instances:
            system.max_instances = len(system.instances)

    system = create(system)

    return system


@publish_event(Events.SYSTEM_UPDATED)
def update_system(system_id: str, operations: Sequence[PatchOperation]) -> System:
    """Update an already existing System

    Args:
        system_id: The ID of the System to be updated
        operations: List of patch operations

    Returns:
        The updated System

    """
    system = query_unique(System, id=system_id)

    for op in operations:
        if op.operation == "replace":
            if op.path == "/commands":
                new_commands = SchemaParser.parse_command(op.value, many=True)

                if (
                    system.commands
                    and "dev" not in system.version
                    and system.has_different_commands(new_commands)
                ):
                    raise ModelValidationError(
                        f"System {system.name}-{system.version} already exists with "
                        f"different commands"
                    )

                # TODO - Move this somewhere
                # system.upsert_commands(new_commands)
            elif op.path in ["/description", "/icon_name", "/display_name"]:
                # If we set an attribute to None mongoengine marks that
                # attribute for deletion, so we don't do that.
                value = "" if op.value is None else op.value
                attr = op.path.strip("/")

                setattr(system, attr, value)

                update(system)
            else:
                raise ModelValidationError(f"Unsupported path for replace '{op.path}'")
        elif op.operation == "add":
            if op.path == "/instance":
                instance = SchemaParser.parse_instance(op.value)

                if len(system.instances) >= system.max_instances:
                    raise ModelValidationError(
                        f"Unable to add instance {instance.name} as it would exceed "
                        f"the system instance limit ({system.max_instances})"
                    )

                system.instances.append(instance)

                create(system)
            else:
                raise ModelValidationError(f"Unsupported path for add '{op.path}'")
        elif op.operation == "update":
            if op.path == "/metadata":
                system.metadata.update(op.value)
                update(system)
            else:
                raise ModelValidationError(f"Unsupported path for update '{op.path}'")
        elif op.operation == "reload":
            return reload_system(system_id)
        else:
            raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    system = reload(system)

    return system


def reload_system(system_id: str) -> None:
    """Reload a system configuration

    Args:
        system_id: The System ID

    Returns:
        None

    """
    system = query_unique(System, id=system_id)

    logger.info("Reloading system: %s-%s", system.name, system.version)
    beer_garden.application.plugin_manager.reload_system(system.name, system.version)


@publish_event(Events.SYSTEM_REMOVED)
def remove_system(system_id: str) -> None:
    """Remove a system

    Args:
        system_id: The System ID

    Returns:
        None

    """
    system = query_unique(System, id=system_id)

    # Attempt to stop the plugins
    registered = beer_garden.application.plugin_registry.get_plugins_by_system(
        system.name, system.version
    )

    # Local plugins get stopped by us
    if registered:
        for plugin in registered:
            beer_garden.application.plugin_manager.stop_plugin(plugin)
            beer_garden.application.plugin_registry.remove(plugin.unique_name)

    # Remote plugins get a stop request
    else:
        beer_garden.application.clients["pika"].publish_request(
            beer_garden.stop_request,
            routing_key=get_routing_key(system.name, system.version, is_admin=True),
        )
        count = 0
        while any(
            instance.status != "STOPPED" for instance in system.instances
        ) and count < beer_garden.config.get("plugin.local.timeout.shutdown"):
            sleep(1)
            count += 1
            system = reload(system)

    system = reload(system)

    # Now clean up the message queues
    for instance in system.instances:

        # It is possible for the request or admin queue to be none if we are
        # stopping an instance that was not properly started.
        request_queue = instance.queue_info.get("request", {}).get("name")
        admin_queue = instance.queue_info.get("admin", {}).get("name")

        beer_garden.application.clients["pyrabbit"].destroy_queue(
            request_queue, force_disconnect=(instance.status != "STOPPED")
        )
        beer_garden.application.clients["pyrabbit"].destroy_queue(
            admin_queue, force_disconnect=(instance.status != "STOPPED")
        )

    # Finally, actually delete the system
    delete(system)


def rescan_system_directory() -> None:
    """Scans plugin directory and starts any new Systems"""
    beer_garden.application.plugin_manager.scan_plugin_path()
