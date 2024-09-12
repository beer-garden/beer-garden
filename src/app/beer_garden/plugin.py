# -*- coding: utf-8 -*-

"""This is the Plugin State Manager

* Plugin Registration
* Plugin Monitoring
* Plugin Removal

Plugins in this case are the abstract concept of plugins. That is to say, the PSM doesn't
know anything about the actual process that is running.  The only distinction the
Plugin State Manager makes is about downstream vs upstream plugins.

It is completely up to the PSM to change a plugin's state
(i.e. is the plugin unresponsive? healthy? running? stopped? etc.)

While the plugin state manager is responsible for initiating status messages, it will
delegate requesting information from the plugin to the request service.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple

from brewtils.models import (
    Event,
    Events,
    Instance,
    Operation,
    Request,
    RequestTemplate,
    System,
)
from brewtils.schema_parser import SchemaParser
from brewtils.stoppable_thread import StoppableThread
from mongoengine import DoesNotExist
from mongoengine.fields import ObjectIdField

import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.db.mongo.motor as moto
import beer_garden.local_plugins.manager as lpm
import beer_garden.queue.api as queue
import beer_garden.requests as requests
from beer_garden.errors import NotFoundException
from beer_garden.events import publish, publish_event, publish_event_async

logger = logging.getLogger(__name__)

start_request = RequestTemplate(command="_start", command_type="EPHEMERAL")
stop_request = RequestTemplate(command="_stop", command_type="EPHEMERAL")
initialize_logging_request = RequestTemplate(
    command="_initialize_logging", command_type="EPHEMERAL"
)
read_logs_request = RequestTemplate(command="_read_log", command_type="TEMP")


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

    logger.debug(f"Initializing instance {system}[{instance}]")

    queue_spec = queue.create(instance, system)

    instance.status_info.set_status_heartbeat(
        instance.status, max_history=config.get("plugin.status_history")
    )

    system = db.modify(
        system,
        query={"instances__name": instance.name},
        **{
            "set__instances__S__status": "INITIALIZING",
            "set__instances__S__status_info": instance.status_info,
            "set__instances__S__metadata__runner_id": runner_id,
            "set__instances__S__queue_type": queue_spec["queue_type"],
            "set__instances__S__queue_info": queue_spec["queue_info"],
        },
    )

    if runner_id:
        lpm.map_runner_to_instance(runner_id, instance.id)

    return system.get_instance_by_name(instance.name)


@publish_event(Events.INSTANCE_STARTED)
def start(
    instance_id: str = None, instance: Instance = None, system: System = None
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

    logger.debug(f"Starting instance {system}[{instance}]")

    # Only way this works is if this has a local runner, so just assume it does
    lpm.start(instance_id=instance.id)

    # Publish the start request
    publish_start(system, instance)

    return instance


@publish_event(Events.INSTANCE_STARTED)
def restart(
    instance_id: str = None, instance: Instance = None, system: System = None
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

    logger.debug(f"Starting instance {system}[{instance}]")

    # Only way this works is if this has a local runner, so just assume it does
    lpm.restart(instance_id=instance.id)

    # Publish the start request
    publish_start(system, instance)

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

    logger.debug(f"Stopping instance {system}[{instance}]")

    # Publish the stop request
    publish_stop(system, instance)

    return instance


def publish_start(system, instance):
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
    )


def publish_stop(system, instance=None):
    request_args = {
        "namespace": system.namespace,
        "system": system.name,
        "system_version": system.version,
    }

    if instance:
        request_args["instance_name"] = instance.name

    requests.process_request(
        Request.from_template(stop_request, **request_args), is_admin=True, priority=1
    )


@publish_event(Events.INSTANCE_UPDATED)
def update(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
    new_status: str = None,
    metadata: dict = None,
    update_heartbeat: bool = True,
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
        update_heartbeat: Set the heartbeat to the current time

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

        if new_status == "STOPPED":
            lpm.update(instance_id=instance_id, restart=False, stopped=True)

    if update_heartbeat:
        instance.status_info.set_status_heartbeat(
            instance.status, max_history=config.get("plugin.status_history")
        )

        updates["set__instances__S__status_info"] = instance.status_info

    if metadata:
        metadata_update = dict(instance.metadata)
        metadata_update.update(metadata)
        updates["set__instances__S__metadata"] = metadata_update

    system = db.modify(system, query={"instances__name": instance.name}, **updates)

    return system.get_instance_by_name(instance.name)


def publish_status_update(instance: Instance):
    """Publish event of Instance status.

    Args:
        instance: The Instance

    """
    system, instance = _from_kwargs(instance_id=instance.id)

    if system.local:
        # Publish event for plugins to monitor the status of other plugins
        publish(
            Event(
                name=Events.REQUEST_TOPIC_PUBLISH.name,
                metadata={
                    "topic": config.get("garden.name"),
                    "propagate": True,
                },
                payload=Request(
                    parameters={
                        "message": {
                            "status": instance.status,
                            "namespace": system.namespace,
                            "system": system.name,
                            "version": system.version,
                            "instance": instance.name,
                            "garden": config.get("garden.name"),
                            "event": Events.INSTANCE_UPDATED.name,
                        }
                    },
                ),
                payload_type="Request",
            )
        )


def heartbeat(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
    **_,
) -> Instance:
    """Instance heartbeat

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

    instance.status_info.set_status_heartbeat(
        instance.status, max_history=config.get("plugin.status_history")
    )

    system = db.modify(
        system,
        query={"instances__name": instance.name},
        set__instances__S__status_info=instance.status_info,
    )

    return system.get_instance_by_name(instance.name)


def initialize_logging(
    instance_id: str = None, instance: Instance = None, system: System = None
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
    )

    return instance


def read_logs_operation(operation: Operation) -> Operation:
    """Converts Operation to Read lines from an Instance's log file.

    Expected Operation.kwargs fields:
        instance_id: The Instance ID
        start_line: Start reading log file at
        end_line: Stop reading log file at
        wait_event: Wait event for response

    Args:
        operation: The Operation to convert to Create Request


    Returns:
        Operation for Request Create
    """
    system, instance = _from_kwargs(
        instance_id=operation.kwargs.get("instance_id", None),
    )

    logger.debug(
        f"Generating operation for Reading Logs from instance {system}[{instance}]"
    )

    return Operation(
        operation_type="REQUEST_CREATE",
        model=Request.from_template(
            read_logs_request,
            namespace=system.namespace,
            system=system.name,
            system_version=system.version,
            instance_name=instance.name,
            parameters={
                "start_line": operation.kwargs.get("start_line", None),
                "end_line": operation.kwargs.get("end_line", None),
            },
        ),
        model_type="Request",
        kwargs={
            "wait_event": operation.kwargs.get("wait_event", None),
            "is_admin": True,
            "priority": 1,
        },
        target_garden_name=operation.target_garden_name,
        source_garden_name=operation.source_garden_name,
        source_api=operation.source_api,
    )


@publish_event_async(Events.INSTANCE_UPDATED)
async def update_async(
    instance_id: str = None,
    instance: Instance = None,
    system: System = None,
    new_status: str = None,
    metadata: dict = None,
    **_,
) -> dict:
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
    query = {"instances._id": ObjectIdField().to_mongo(instance_id)}
    projection = {"instances.$": 1, "_id": 0}
    update = {}
    push = {}

    if new_status:
        update["instances.$.status"] = new_status
        update["instances.$.status_info.heartbeat"] = datetime.utcnow()
        push["instances.$.status_info.history"] = {
            "status": new_status,
            "heartbeat": datetime.utcnow(),
        }

        if new_status == "STOPPED":
            lpm.update(instance_id=instance_id, restart=False, stopped=True)

    if metadata:
        for k, v in metadata.items():
            update[f"instances.$.metadata.{k}"] = v

    return await _update_instance_async(
        query, projection, {"$set": update, "$push": push}
    )


async def heartbeat_async(
    instance_id: str = None, instance: Instance = None, system: System = None, **_
) -> dict:
    query = {"instances._id": ObjectIdField().to_mongo(instance_id)}
    projection = {"instances.$": 1, "_id": 0}
    update = {
        "$set": {"instances.$.status_info.heartbeat": datetime.utcnow()},
        "$push": {
            "instances.$.status_info.history": {
                "status": "RUNNING",
                "heartbeat": datetime.utcnow(),
            }
        },
    }

    return await _update_instance_async(query, projection, update)


async def _get_instance_async(filter, projection) -> dict:
    """Helper to get an instance async-style"""
    result = await moto.query(collection="system", filter=filter, projection=projection)

    # TODO - This is not the best
    instance = result["instances"][0]
    if "_id" in instance:
        instance["id"] = str(instance["_id"])
        del instance["_id"]

    if config.get("plugin.status_history") > 0 and len(
        instance["status_info"]["history"]
    ) > config.get("plugin.status_history"):
        return await _update_instance_async(
            filter,
            projection,
            {
                "$set": {
                    "instances.$.status_info.history": instance["status_info"][
                        "history"
                    ][-1 * config.get("plugin.status_history") :]
                }
            },
        )

    return SchemaParser.parse_instance(instance)


async def _update_instance_async(filter, projection, update) -> dict:
    """Helper to update an instance async-style"""
    await moto.update_one(collection="system", filter=filter, update=update)

    return await _get_instance_async(filter, projection)


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

    if event.name == Events.INSTANCE_UPDATED.name:
        if not event.payload_type:
            logger.error(f"{event.name} error: no payload type ({event!r})")
            return

        if event.garden != config.get("garden.name"):
            try:
                update(
                    instance_id=event.payload.id,
                    new_status=event.payload.status,
                    metadata=event.payload.metadata,
                )
            except DoesNotExist:
                logger.error(
                    (
                        "Unable to find system matching instance "
                        f"{event.payload.id}:{event.payload.name} "
                        f"for garden {event.garden}"
                    )
                )
                from beer_garden.router import route

                route(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        target_garden_name=event.garden,
                        kwargs={"sync_target": event.garden},
                    )
                )
            except Exception as ex:
                logger.error(f"{event.name} error: {ex} ({event!r})")
        else:
            publish_status_update(event.payload)


class StatusMonitor(StoppableThread):
    """Monitor plugin heartbeats and update plugin status"""

    def __init__(self, heartbeat_interval=10, timeout_seconds=30):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Plugin Status Monitor"
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timedelta(seconds=timeout_seconds)
        self.status_request = Request(command="_status", command_type="EPHEMERAL")

        super(StatusMonitor, self).__init__(
            logger=self.logger, name="PluginStatusMonitor"
        )

    def run(self):
        self.logger.debug(self.display_name + " is started")

        while not self.wait(self.heartbeat_interval):
            self.request_status()
            self.check_status()

        self.logger.debug(self.display_name + " is stopped")

    def request_status(self):
        try:
            queue.put(
                self.status_request,
                routing_key="admin",
                expiration=str(self.heartbeat_interval * 1000),
            )
        except Exception as ex:
            self.logger.warning("Unable to publish status request: %s", str(ex))

    def check_status(self):
        """Update instance status if necessary"""

        for system in db.query(
            System, filter_params={"local": True}, include_fields=["instances"]
        ):
            for instance in system.instances:
                if self.stopped():
                    break

                last_heartbeat = instance.status_info.heartbeat

                if last_heartbeat:
                    if (
                        instance.status == "RUNNING"
                        and datetime.utcnow() - last_heartbeat >= self.timeout
                    ):
                        update(
                            system=system,
                            instance=instance,
                            new_status="UNRESPONSIVE",
                            update_heartbeat=False,
                        )

                    elif (
                        instance.status
                        in ["UNRESPONSIVE", "STARTING", "INITIALIZING", "UNKNOWN"]
                        and datetime.utcnow() - last_heartbeat < self.timeout
                    ):
                        update(
                            system=system,
                            instance=instance,
                            new_status="RUNNING",
                            update_heartbeat=False,
                        )
