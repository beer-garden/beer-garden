# -*- coding: utf-8 -*-
"""Queue Service

The queue service is responsible for:

* Queue CRUD operations
* Publishing requests

Much like the persistence layer, the queue service helps keep the rest of the subsystems
from understanding anything about the queueing mechanism being used by a particular system.
As such, it is responsible for providing an API which is consistent across each queue
technology we use.
"""

import logging

from brewtils.models import Events, Queue, System, Instance

import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.events import publish_event
from beer_garden.queue.rabbit import get_routing_key

logger = logging.getLogger(__name__)


def get_queue_message_count(queue_name):
    """Gets the size of a queue

    :param queue_name: The queue name
    :return: number of messages currently on the queue
    :raises Exception: If queue does not exist
    """
    return queue.count(queue_name)


def get_instance_queues(instance_id):
    instance = db.query_unique(Instance, id=instance_id)

    if instance.queue_info:

        request_queue = Queue(
            name=instance.queue_info["request"]["name"], instance=instance.name, size=-1
        )

        try:
            request_queue.size = get_queue_message_count(
                instance.queue_info["request"]["name"]
            )
        except Exception:
            logger.error(
                f"Error getting queue size for {instance.queue_info['request']['name']}"
            )

        queues = [request_queue]

    return queues


def get_all_queue_info():
    """Get queue information for all queues

    :return size of the queue
    :raises Exception: If queue does not exist
    """
    queues = []
    systems = db.query(System)

    for system in systems:
        for instance in system.instances:
            queue_name = get_routing_key(
                system.namespace, system.name, system.version, instance.name
            )

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
    queue.clear(queue_name)


@publish_event(Events.ALL_QUEUES_CLEARED)
def clear_all_queues():
    """Clears all queues that Bartender knows about.

    :return: None
    """
    systems = db.query(System)

    for system in systems:
        for instance in system.instances:
            routing_key = get_routing_key(
                system.namespace, system.name, system.version, instance.name
            )
            clear_queue(routing_key)
