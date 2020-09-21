# -*- coding: utf-8 -*-

"""This is the Plugin State Manager"""

import logging
from datetime import datetime
from typing import Tuple

from brewtils.models import Event, Events, Instance, Request, RequestTemplate, System

import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.queue.api as queue
import beer_garden.requests as requests
from beer_garden.errors import NotFoundException
from beer_garden.events import publish_event

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
    **_,
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
    system, instance = _from_kwargs(
        system=system, instance=instance, instance_id=instance_id
    )

    logger.info(f"Initializing instance {system}[{instance}]")

    queue_spec = queue.create(instance, system)

    system = db.modify(
        system,
        query={"instances__name": instance.name},
        **{
            "set__instances__S__status": "INITIALIZING",
            "set__instances__S__status_info__heartbeat": datetime.utcnow(),
            "set__instances__S__metadata__runner_id": runner_id,
            "set__instances__S__queue_type": queue_spec["queue_type"],
            "set__instances__S__queue_info": queue_spec["queue_info"],
        },
    )

    start(instance=instance, system=system)

    return system.get_instance_by_name(instance.name)


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
    system, instance = _from_kwargs(
        system=system, instance=instance, instance_id=instance_id
    )

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
    system, instance = _from_kwargs(
        system=system, instance=instance, instance_id=instance_id
    )

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
    system, instance = _from_kwargs(
        system=system, instance=instance, instance_id=instance_id
    )

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
    **_,
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
    system, instance = _from_kwargs(
        system=system, instance=instance, instance_id=instance_id
    )

    logger.debug(f"Updating instance {system}[{instance}]")

    updates = {}

    if new_status:
        updates["set__instances__S__status"] = new_status
        updates["set__instances__S__status_info__heartbeat"] = datetime.utcnow()

    if metadata:
        metadata_update = dict(instance.metadata)
        metadata_update.update(metadata)
        updates["set__instances__S__metadata"] = metadata_update

    system = db.modify(system, query={"instances__name": instance.name}, **updates)

    return system.get_instance_by_name(instance.name)


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
    system, instance = _from_kwargs(
        system=system, instance=instance, instance_id=instance_id
    )

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


def _from_kwargs(
    system: System = None,
    instance: Instance = None,
    system_id: str = None,
    instance_name: str = None,
    instance_id: str = None,
    **_,
) -> Tuple[System, Instance]:

    if system and instance:
        return system, instance

    if not system:
        if system_id:
            system = db.query_unique(System, raise_missing=True, id=system_id)
        elif instance:
            system = db.query_unique(
                System, raise_missing=True, instances__contains=instance
            )
        elif instance_id:
            system = db.query_unique(
                System, raise_missing=True, instances__id=instance_id
            )
        else:
            raise NotFoundException("Unable to find System")

    if not instance:
        if instance_name:
            instance = system.get_instance_by_name(instance_name)
        elif instance_id:
            instance = system.get_instance_by_id(instance_id)
        else:
            raise NotFoundException("Unable to find Instance")

    return system, instance


def handle_event(event: Event) -> None:
    """Handle INSTANCE events

    Args:
        event: The event to handle
    """
    if event.garden != config.get("garden.name"):

        if event.name == Events.INSTANCE_UPDATED.name:
            if not event.payload_type:
                logger.error(f"{event.name} error: no payload type ({event!r})")
                return

            try:
                update(
                    instance_id=event.payload.id,
                    new_status=event.payload.status,
                    metadata=event.payload.metadata,
                )
            except Exception as ex:
                logger.error(f"{event.name} error: {ex} ({event!r})")
