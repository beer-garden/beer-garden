# -*- coding: utf-8 -*-

"""This is the Plugin State Manager"""

import logging
from datetime import datetime

from brewtils.models import Events, Instance, Request, RequestTemplate, System

import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.events import publish_event
import beer_garden.requests as requests

logger = logging.getLogger(__name__)

start_request = RequestTemplate(command="_start", command_type="EPHEMERAL")
stop_request = RequestTemplate(command="_stop", command_type="EPHEMERAL")
initialize_logging_request = RequestTemplate(
    command="_initialize_logging", command_type="EPHEMERAL"
)
read_logs_request = RequestTemplate(command="_read_log", command_type="ADMIN")


@publish_event(Events.INSTANCE_INITIALIZED)
def initialize(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
    runner_id: str = None,
) -> Instance:
    """Initializes an instance.

    Args:
        instance_id: The Instance ID
        instance: The Instance
        system: The System
        runner_id: The runner id to associate with this plugin, if any

    Returns:
        The updated Instance
    """
    instance = instance or db.query_unique(Instance, id=instance_id)
    system = system or db.query_unique(System, instances__contains=instance)

    logger.info(f"Initializing instance {system}[{instance}]")

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
def start(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
) -> Instance:
    """Starts an instance.

    Args:
        instance_id: The Instance ID
        instance: The Instance
        system: The System

    Returns:
        The updated Instance
    """
    instance = instance or db.query_unique(Instance, id=instance_id)
    system = system or db.query_unique(System, instances__contains=instance)

    logger.info(f"Starting instance {system}[{instance}]")

    requests.process_request(
        Request.from_template(
            start_request,
            namespace=system.namespace,
            system=system.name,
            system_version=system.version,
            instance_name=instance.name,
        ),
        is_admin=True,
        priority=1,
        wait_timeout=0,
    )

    return instance


@publish_event(Events.INSTANCE_STOPPED)
def stop(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
) -> Instance:
    """Stops an Instance.

    Args:
        instance_id: The Instance ID
        instance: The Instance
        system: The System

    Returns:
        The updated Instance
    """
    instance = instance or db.query_unique(Instance, id=instance_id)
    system = system or db.query_unique(System, instances__contains=instance)

    logger.info(f"Stopping instance {system}[{instance}]")

    requests.process_request(
        Request.from_template(
            stop_request,
            namespace=system.namespace,
            system=system.name,
            system_version=system.version,
            instance_name=instance.name,
        ),
        is_admin=True,
        priority=1,
        wait_timeout=0,
    )

    return instance


def initialize_logging(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
) -> Instance:
    """Initialize logging of Instance.

    Args:
        instance_id: The Instance ID
        instance: The Instance
        system: The System

    Returns:
        The Instance
    """
    instance = instance or db.query_unique(Instance, id=instance_id)
    system = system or db.query_unique(System, instances__contains=instance)

    logger.debug(f"Initializing logging for instance {system}[{instance}]")

    requests.process_request(
        Request.from_template(
            initialize_logging_request,
            namespace=system.namespace,
            system=system.name,
            system_version=system.version,
            instance_name=instance.name,
        ),
        is_admin=True,
        priority=1,
        wait_timeout=0,
    )

    return instance


@publish_event(Events.INSTANCE_UPDATED)
def update(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
    new_status: str = None,
    metadata: dict = None,
) -> Instance:
    """Update an Instance status.

    Will also update the status_info heartbeat.

    Args:
        instance_id: The Instance ID
        instance: The Instance
        system: The System
        new_status: The new status
        metadata: New metadata

    Returns:
        The updated Instance
    """
    instance = instance or db.query_unique(Instance, id=instance_id)
    system = system or db.query_unique(System, instances__contains=instance)

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


def read_logs(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
    start_line: int = None,
    end_line: int = None,
    wait_timeout: float = -1,
) -> Request:
    """Read lines from an Instance's log file.

    Args:
        instance_id: The Instance ID
        instance: The Instance
        system: The System
        start_line: Start reading log file at
        end_line: Stop reading log file at
        wait_timeout: Wait timeout for response

    Returns:
        Request object with logs as output
    """
    instance = instance or db.query_unique(Instance, id=instance_id)
    system = system or db.query_unique(System, instances__contains=instance)

    logger.debug(f"Reading Logs from instance {system}[{instance}]")

    request = requests.process_request(
        Request.from_template(
            read_logs_request,
            namespace=system.namespace,
            system=system.name,
            system_version=system.version,
            instance_name=instance.name,
            parameters={"start_line": start_line, "end_line": end_line},
        ),
        is_admin=True,
        wait_timeout=wait_timeout,
    )

    return request
