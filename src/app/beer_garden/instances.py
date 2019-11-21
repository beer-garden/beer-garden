# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from brewtils.errors import ModelValidationError
from brewtils.models import Events, Instance, PatchOperation, System, Request

import beer_garden
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.events.events_manager import publish_event

logger = logging.getLogger(__name__)


def get_instance(instance_id: str) -> Instance:
    """Retrieve an individual Instance

    Args:
        instance_id: The Instance ID

    Returns:
        The Instance

    """
    return db.query_unique(Instance, id=instance_id)


@publish_event(Events.INSTANCE_INITIALIZED)
def initialize_instance(instance_id: str) -> Instance:
    """Initializes an instance.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(
        f"Initializing instance {system.name}[{instance.name}]-{system.version}"
    )

    queue_spec = queue.create(instance)

    instance.status = "INITIALIZING"
    instance.status_info = {"heartbeat": datetime.utcnow()}
    instance.queue_type = queue_spec["queue_type"]
    instance.queue_info = queue_spec["queue_info"]

    instance = db.update(instance)

    start_instance(instance_id)

    return instance


def update_instance(instance_id: str, patch: PatchOperation) -> Instance:
    """Applies updates to an instance.

    Args:
        instance_id: The Instance ID
        patch: Patch definition to apply

    Returns:
        The updated Instance
    """
    instance = None

    for op in patch:
        operation = op.operation.lower()

        if operation == "initialize":
            instance = initialize_instance(instance_id)

        elif operation == "start":
            instance = start_instance(instance_id)

        elif operation == "stop":
            instance = stop_instance(instance_id)

        elif operation == "heartbeat":
            instance = update_instance_status(instance_id, "RUNNING")

        elif operation == "replace":
            if op.path.lower() == "/status":
                instance = update_instance_status(instance_id, op.value)
            else:
                raise ModelValidationError(f"Unsupported path '{op.path}'")
        else:
            raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    return instance


@publish_event(Events.INSTANCE_STARTED)
def start_instance(instance_id: str) -> Instance:
    """Starts an instance.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(f"Starting instance {system.name}[{instance.name}]-{system.version}")

    # Send a request to start to the plugin on the plugin's admin queue
    request = Request.from_template(
        beer_garden.start_request,
        system=system.name,
        system_version=system.version,
        instance_name=instance.name,
    )
    queue.put(request, is_admin=True)

    # beer_garden.application.plugin_manager.start_plugin(
    #     beer_garden.application.plugin_registry.get_plugin_from_instance_id(instance.id)
    # )

    return instance


@publish_event(Events.INSTANCE_STOPPED)
def stop_instance(instance_id: str) -> Instance:
    """Stops an Instance.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(f"Stopping instance {system.name}[{instance.name}]-{system.version}")

    request = Request.from_template(
        beer_garden.stop_request,
        system=system.name,
        system_version=system.version,
        instance_name=instance.name,
    )
    queue.put(request, is_admin=True)

    # local_plugin = beer_garden.application.plugin_registry.get_plugin_from_instance_id(
    #     instance.id
    # )
    #
    # if local_plugin:
    #     beer_garden.application.plugin_manager.stop_plugin(local_plugin)
    # else:
    #     # This causes the request consumer to terminate itself, which ends the plugin
    #     queue.put(
    #         beer_garden.stop_request,
    #         routing_key=get_routing_key(
    #             system.name, system.version, instance.name, is_admin=True
    #         ),
    #     )

    return instance


def update_instance_status(instance_id: str, new_status: str) -> Instance:
    """Update an Instance status.

    Will also update the status_info heartbeat.

    Args:
        instance_id: The Instance ID
        new_status: The new status

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    instance.status = new_status
    instance.status_info["heartbeat"] = datetime.utcnow()

    instance = db.update(instance)

    return instance


def remove_instance(instance_id: str) -> None:
    """Removes an Instance

    Args:
        instance_id: The Instance ID

    Returns:
        None
    """
    db.delete(db.query_unique(Instance, id=instance_id))
