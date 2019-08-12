import logging

from pyrabbit2.http import HTTPError

import bartender
from bartender.events import publish_event
from bartender.pika import get_routing_key
from bg_utils.mongo.models import System
from brewtils.errors import NotFoundError
from brewtils.models import Queue, Events

logger = logging.getLogger(__name__)


def get_queue_message_count(queue_name):
    """Gets the size of a queue

    :param queue_name: The queue name
    :return: number of messages currently on the queue
    :raises Exception: If queue does not exist
    """
    logger.debug(f"Getting queue message count for {queue_name}")

    return bartender.application.clients["pyrabbit"].get_queue_size(queue_name)


def get_all_queue_info():
    """Get queue information for all queues

    :return size of the queue
    :raises Exception: If queue does not exist
    """
    queues = []
    systems = System.objects.all().select_related(max_depth=1)

    for system in systems:
        for instance in system.instances:
            queue_name = get_routing_key(system.name, system.version, instance.name)

            queue = Queue(
                name=queue_name,
                system=system.name,
                version=system.version,
                instance=instance.name,
                system_id=str(system.id),
                display=system.display_name,
                size=-1,
            )

            try:
                queue.size = get_queue_message_count(queue_name)
            except Exception:
                logger.error(f"Error getting queue size for {queue_name}")

            queues.append(queue)

    return queues


@publish_event(Events.QUEUE_CLEARED)
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


@publish_event(Events.ALL_QUEUES_CLEARED)
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
