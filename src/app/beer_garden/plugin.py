# -*- coding: utf-8 -*-

"""This is the Plugin State Manager"""

import logging
from datetime import datetime

from brewtils.models import Events, Instance, Request, System

import beer_garden
import beer_garden.config
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.errors import RoutingRequestException
from beer_garden.events.events_manager import publish_event
from beer_garden.router import Route_Type

logger = logging.getLogger(__name__)


def route_request(
    brewtils_obj=None, obj_id: str = None, route_type: Route_Type = None, **kwargs
):

    if route_type is Route_Type.UPDATE:
        if brewtils_obj is None:
            raise RoutingRequestException(
                "An Object is required to route UPDATE request for Instances"
            )
        return update(obj_id, brewtils_obj)
    else:
        raise RoutingRequestException(
            "%s Route for Instances does not exist" % route_type.value
        )


@publish_event(Events.INSTANCE_INITIALIZED)
def initialize(instance_id: str, runner_id: str = None) -> Instance:
    """Initializes an instance.

    Args:
        instance_id: The Instance ID
        runner_id: The runner id to associate with this plugin, if any

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

    # This is ridiculous - Mongoengine strikes again
    metadata = dict(instance.metadata)
    metadata.update({"runner_id": runner_id})
    instance.metadata = metadata

    instance = db.update(instance)

    start(instance_id)

    return instance


@publish_event(Events.INSTANCE_STARTED)
def start(instance_id: str) -> Instance:
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
        namespace=system.namespace,
        system=system.name,
        system_version=system.version,
        instance_name=instance.name,
    )
    queue.put(request, is_admin=True)

    return instance


@publish_event(Events.INSTANCE_STOPPED)
def stop(instance_id: str) -> Instance:
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
        namespace=system.namespace,
        system=system.name,
        system_version=system.version,
        instance_name=instance.name,
    )
    queue.put(request, is_admin=True)

    return instance


@publish_event(Events.INSTANCE_UPDATED)
def update(instance_id: str, new_status: str = None, metadata: dict = None) -> Instance:
    """Update an Instance status.

    Will also update the status_info heartbeat.

    Args:
        instance_id: The Instance ID
        new_status: The new status
        metadata: New metadata

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)

    if new_status:
        instance.status = new_status
        instance.status_info["heartbeat"] = datetime.utcnow()

    # This is ridiculous - Mongoengine strikes again
    if metadata:
        existing_metadata = dict(instance.metadata)
        existing_metadata.update(metadata)
        instance.metadata = existing_metadata

    instance = db.update(instance)

    return instance
