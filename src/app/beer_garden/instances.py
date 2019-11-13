# -*- coding: utf-8 -*-
import logging
import random
import string
from datetime import datetime

from brewtils.errors import ModelValidationError
from brewtils.models import Events, Instance, PatchOperation, System

import beer_garden
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.events import publish_event
from beer_garden.queue.rabbit import get_routing_key, get_routing_keys

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

    This does a lot of stuff right now.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(
        "Initializing instance %s[%s]-%s", system.name, instance.name, system.version
    )

    routing_words = [system.name, system.version, instance.name]

    request_queue_name = get_routing_key(*routing_words)
    request_queue = queue.create(
        request_queue_name,
        [request_queue_name],
        durable=True,
        arguments={"x-max-priority": 1},
    )

    suffix = [random.choice(string.ascii_lowercase + string.digits) for _ in range(10)]
    routing_words.append("".join(suffix))

    admin_keys = get_routing_keys(*routing_words, is_admin=True)
    admin_queue = queue.create(admin_keys[-1], admin_keys, durable=True)

    amq_config = beer_garden.config.get("amq")
    connection = {
        "host": beer_garden.config.get("publish_hostname"),
        "port": amq_config.connections.message.port,
        "user": amq_config.connections.message.user,
        "password": amq_config.connections.message.password,
        "virtual_host": amq_config.virtual_host,
        "ssl": {"enabled": amq_config.connections.message.ssl.enabled},
    }

    instance.status = "INITIALIZING"
    instance.status_info = {"heartbeat": datetime.utcnow()}
    instance.queue_type = "rabbitmq"
    instance.queue_info = {
        "admin": {"name": admin_queue.name},
        "request": {"name": request_queue.name},
        "connection": connection,
    }
    instance = db.update(instance)

    # Send a request to start to the plugin on the plugin's admin queue
    queue.put(
        beer_garden.start_request,
        routing_key=get_routing_key(
            system.name, system.version, instance.name, is_admin=True
        ),
    )

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

    logger.info(
        "Starting instance %s[%s]-%s", system.name, instance.name, system.version
    )

    beer_garden.application.plugin_manager.start_plugin(
        beer_garden.application.plugin_registry.get_plugin_from_instance_id(instance.id)
    )

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

    logger.info(
        "Stopping instance %s[%s]-%s", system.name, instance.name, system.version
    )

    local_plugin = beer_garden.application.plugin_registry.get_plugin_from_instance_id(
        instance.id
    )

    if local_plugin:
        beer_garden.application.plugin_manager.stop_plugin(local_plugin)
    else:
        # This causes the request consumer to terminate itself, which ends the plugin
        queue.put(
            beer_garden.stop_request,
            routing_key=get_routing_key(
                system.name, system.version, instance.name, is_admin=True
            ),
        )

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
