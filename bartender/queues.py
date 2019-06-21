import logging

from pyrabbit2.http import HTTPError

import bartender
from bg_utils.mongo.models import System
from bg_utils.pika import get_routing_key
from brewtils.errors import NotFoundError

logger = logging.getLogger(__name__)


def get_queue_info(system_name, system_version, instance_name):
    """Gets the size of a queue

    :param system_name: The system name
    :param system_version: The system version
    :param instance_name: The instance name
    :return size of the queue
    :raises Exception: If queue does not exist
    """
    routing_key = get_routing_key(system_name, system_version, instance_name)
    logger.debug("Get the queue state for %s", routing_key)

    return (
        routing_key,
        bartender.application.clients["pyrabbit"].get_queue_size(routing_key),
    )


def clear_queue(queue_name):
    """Clear all Requests in the given queue

    Will iterate through all requests on a queue and mark them as "CANCELED".

    :param queue_name: The queue to clean
    :raises InvalidSystem: If the system_name/instance_name does not match a queue
    """
    logger.debug("Clearing queue %s", queue_name)
    try:
        bartender.application.clients["pyrabbit"].clear_queue(queue_name)
    except HTTPError as ex:
        if ex.status == 404:
            raise NotFoundError("No queue named %s" % queue_name)
        else:
            raise


def clear_all_queues():
    """Clears all queues that Bartender knows about.

    :return: None
    """
    logger.debug("Clearing all queues")
    systems = System.objects.all()

    for system in systems:
        for instance in system.instances:
            routing_key = get_routing_key(system.name, system.version, instance.name)
            clear_queue(routing_key)
