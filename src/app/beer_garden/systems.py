import logging
from time import sleep
from typing import List, Sequence, Dict

import brewtils.models
from brewtils.errors import ModelValidationError
from brewtils.models import Events
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import SystemSchema

import beer_garden
from beer_garden.bg_utils.mongo.models import System, Instance
from beer_garden.bg_utils.mongo.parser import MongoParser
from beer_garden.events import publish_event
from beer_garden.rabbitmq import get_routing_key

REQUEST_FIELDS = set(SystemSchema.get_attribute_names())

# system_lock = RLock()
parser = MongoParser()

logger = logging.getLogger(__name__)


def get_system(system_id: str) -> brewtils.models.System:
    """Retrieve an individual System

    Args:
        system_id: The System ID

    Returns:
        The System

    """
    return SchemaParser.parse_system(
        SchemaParser.serialize_system(
            System.objects.get(id=system_id), to_string=False
        ),
        from_string=False,
    )


def query_systems(
    filter_params: Dict[str, str] = None,
    order_by: str = "name",
    include_fields: Sequence[str] = None,
    exclude_fields: Sequence[str] = None,
    dereference_nested: bool = True,
) -> List[brewtils.models.System]:
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
    query_set = System.objects.order_by(order_by)

    if include_fields:
        query_set = query_set.only(*include_fields)

    if exclude_fields:
        query_set = query_set.exclude(*exclude_fields)

    if not dereference_nested:
        query_set = query_set.no_dereference()

    filtered = query_set.filter(**(filter_params or {}))

    return SchemaParser.parse_system(
        SchemaParser.serialize_system(filtered, to_string=False, many=True),
        from_string=False,
        many=True,
    )


@publish_event(Events.SYSTEM_CREATED)
def create_system(system: brewtils.models.System) -> brewtils.models.System:
    """Create a new System

    Args:
        system: The System to create

    Returns:
        The created System

    """
    system = MongoParser.parse_system(
        SchemaParser.serialize_system(system, to_string=False), from_string=False
    )

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

    system.deep_save()

    return SchemaParser.parse_system(
        MongoParser.serialize_system(system, to_string=False), from_string=False
    )


@publish_event(Events.SYSTEM_UPDATED)
def update_system(
    system_id: str, operations: Sequence[brewtils.models.PatchOperation]
) -> brewtils.models.System:
    """Update an already existing System

    Args:
        system_id: The ID of the System to be updated
        operations: List of patch operations

    Returns:
        The updated System

    """
    system = System.objects.get(id=system_id)

    for op in operations:
        if op.operation == "replace":
            if op.path == "/commands":
                new_commands = parser.parse_command(op.value, many=True)

                if (
                    system.commands
                    and "dev" not in system.version
                    and system.has_different_commands(new_commands)
                ):
                    raise ModelValidationError(
                        f"System {system.name}-{system.version} already exists with "
                        f"different commands"
                    )

                system.upsert_commands(new_commands)
            elif op.path in ["/description", "/icon_name", "/display_name"]:
                # If we set an attribute to None mongoengine marks that
                # attribute for deletion, so we don't do that.
                value = "" if op.value is None else op.value
                attr = op.path.strip("/")

                setattr(system, attr, value)

                system.save()
            else:
                raise ModelValidationError(f"Unsupported path for replace '{op.path}'")
        elif op.operation == "add":
            if op.path == "/instance":
                instance = parser.parse_instance(op.value)

                if len(system.instances) >= system.max_instances:
                    raise ModelValidationError(
                        f"Unable to add instance {instance.name} as it would exceed "
                        f"the system instance limit ({system.max_instances})"
                    )

                system.instances.append(instance)
                system.deep_save()
            else:
                raise ModelValidationError(f"Unsupported path for add '{op.path}'")
        elif op.operation == "update":
            if op.path == "/metadata":
                system.metadata.update(op.value)
                system.save()
            else:
                raise ModelValidationError(f"Unsupported path for update '{op.path}'")
        elif op.operation == "reload":
            return reload_system(system_id)
        else:
            raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    system.reload()

    return SchemaParser.parse_system(
        MongoParser.serialize_system(system, to_string=False), from_string=False
    )


def reload_system(system_id: str) -> None:
    """Reload a system configuration

    Args:
        system_id: The System ID

    Returns:
        None

    """
    system = System.objects.get(id=system_id)

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
    system = System.objects.get(id=system_id)

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
            system.reload()

    system.reload()

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
    system.deep_delete()


def rescan_system_directory() -> None:
    """Scans plugin directory and starts any new Systems"""
    beer_garden.application.plugin_manager.scan_plugin_path()
