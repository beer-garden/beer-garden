import logging
import random
import string

from datetime import datetime

import bartender
from bartender.events import publish_event
from bartender.rabbitmq import get_routing_key, get_routing_keys
from bg_utils.mongo.fields import StatusInfo
from bg_utils.mongo.models import Instance, System
from brewtils.errors import ModelValidationError
from brewtils.models import Events

logger = logging.getLogger(__name__)


def get_instance(instance_id):
    return Instance.objects.get(id=instance_id)


@publish_event(Events.INSTANCE_INITIALIZED)
def initialize_instance(instance_id):
    """Initializes an instance.

    :param instance_id: The ID of the instance
    :return: QueueInformation object describing message queue for this system
    """
    instance = Instance.objects.get(id=instance_id)
    system = System.objects.get(instances__contains=instance)

    logger.info(
        "Initializing instance %s[%s]-%s", system.name, instance.name, system.version
    )

    routing_words = [system.name, system.version, instance.name]
    req_name = get_routing_key(*routing_words)
    req_args = {"durable": True, "arguments": {"x-max-priority": 1}}
    req_queue = bartender.application.clients["pika"].setup_queue(
        req_name, req_args, [req_name]
    )

    routing_words.append(
        "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(10)
        )
    )
    admin_keys = get_routing_keys(*routing_words, is_admin=True)
    admin_args = {"auto_delete": True}
    admin_queue = bartender.application.clients["pika"].setup_queue(
        admin_keys[-1], admin_args, admin_keys
    )

    connection = {
        "host": bartender.config.publish_hostname,
        "port": bartender.config.amq.connections.message.port,
        "user": bartender.config.amq.connections.message.user,
        "password": bartender.config.amq.connections.message.password,
        "virtual_host": bartender.config.amq.virtual_host,
        "ssl": {"enabled": bartender.config.amq.connections.message.ssl.enabled},
    }

    instance.status = "INITIALIZING"
    instance.status_info = StatusInfo(heartbeat=datetime.utcnow())
    instance.queue_type = "rabbitmq"
    instance.queue_info = {
        "admin": admin_queue,
        "request": req_queue,
        "connection": connection,
        "url": bartender.application.clients["public"].connection_url,
    }
    instance.save()

    # Send a request to start to the plugin on the plugin's admin queue
    bartender.application.clients["pika"].start(
        system=system.name, version=system.version, instance=instance.name
    )

    return instance


def update_instance(instance_id, patch):
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
def start_instance(instance_id):
    """Starts an instance.

    :param instance_id: The Instance id
    :return: None
    """
    instance = Instance.objects.get(id=instance_id)
    system = System.objects.get(instances__contains=instance)

    logger.info(
        "Starting instance %s[%s]-%s", system.name, instance.name, system.version
    )

    bartender.application.plugin_manager.start_plugin(
        bartender.application.plugin_registry.get_plugin_from_instance_id(instance.id)
    )

    return instance


@publish_event(Events.INSTANCE_STOPPED)
def stop_instance(instance_id):
    """Stops an instance.

    :param instance_id: The Instance id
    :return: None
    """
    instance = Instance.objects.get(id=instance_id)
    system = System.objects.get(instances__contains=instance)

    logger.info(
        "Stopping instance %s[%s]-%s", system.name, instance.name, system.version
    )

    local_plugin = bartender.application.plugin_registry.get_plugin_from_instance_id(
        instance.id
    )

    if local_plugin:
        bartender.application.plugin_manager.stop_plugin(local_plugin)
    else:
        system = System.objects.get(instances__contains=instance)

        # This causes the request consumer to terminate itself, which ends the plugin
        bartender.application.clients["pika"].stop(
            system=system.name, version=system.version, instance=instance.name
        )

    return instance


def update_instance_status(instance_id, new_status):
    """Update an instance status.

    Will also update the status_info heartbeat.

    Args:
        instance_id: The instance ID
        new_status: The new status

    Returns:
        The updated instance
    """
    instance = Instance.objects.get(id=instance_id)
    instance.status = new_status
    instance.status_info.heartbeat = datetime.utcnow()
    instance.save()

    return instance


def remove_instance(instance_id):
    """Removes an instance

    Args:
        instance_id: The instance ID

    Returns:
        None
    """
    Instance.objects.get(id=instance_id).delete()
