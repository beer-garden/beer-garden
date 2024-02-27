# -*- coding: utf-8 -*-
"""Garden Service

The garden service is responsible for:

* Generating local `Garden` record
* Getting `Garden` objects from the database
* Updating `Garden` objects in the database
* Responding to `Garden` sync requests and forwarding request to children
* Handling `Garden` events
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from brewtils.errors import PluginError
from brewtils.models import Connection, Event, Events, Garden, Operation, System
from mongoengine import DoesNotExist
from yapconf.exceptions import (
    YapconfItemNotFound,
    YapconfLoadError,
    YapconfSourceError,
    YapconfSpecError,
)

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.command_publishing_blocklist import (
    publish_command_publishing_blocklist,
)
from beer_garden.db.mongo.models import RemoteUser
from beer_garden.errors import ForwardException
from beer_garden.events import publish, publish_event
from beer_garden.namespace import get_namespaces
from beer_garden.systems import get_systems, remove_system

logger = logging.getLogger(__name__)


def filter_router_result(garden: Garden) -> Garden:
    """Filter values for API output"""
    config_whitelist = [
        "host",
        "port",
        "url_prefix",
        "send_destination",
        "subscribe_destination",
    ]

    if garden.publishing_connections:
        for connection in garden.publishing_connections:
            drop_keys = []
            for key in connection.config:
                if key not in config_whitelist:
                    drop_keys.append(key)
            for key in drop_keys:
                connection.config.pop(key)

    if garden.receiving_connections:
        for connection in garden.receiving_connections:
            drop_keys = []
            for key in connection.config:
                if key not in config_whitelist:
                    drop_keys.append(key)
            for key in drop_keys:
                connection.config.pop(key)

    if garden.children:
        for child in garden.children:
            filter_router_result(child)
    return garden


def get_children_garden(garden: Garden) -> Garden:
    if garden.connection_type == "LOCAL":
        garden.children = db.query(
            Garden, filter_params={"connection_type__ne": "LOCAL", "has_parent": False}
        )
        if garden.children:
            for child in garden.children:
                child.has_parent = True
                child.parent = garden.name
    else:
        garden.children = db.query(Garden, filter_params={"parent": garden.name})

    if garden.children:
        for child in garden.children:
            get_children_garden(child)
    else:
        garden.children = []

    return garden


def get_garden(garden_name: str) -> Garden:
    """Retrieve an individual Garden

    Args:
        garden_name: The name of Garden

    Returns:
        The Garden

    """
    if garden_name == config.get("garden.name"):
        garden = local_garden()
    else:
        garden = db.query_unique(Garden, name=garden_name, raise_missing=True)
    get_children_garden(garden)
    return garden


def get_gardens(include_local: bool = True) -> List[Garden]:
    """Retrieve list of all Gardens

    Args:
        include_local: Also include the local garden

    Returns:
        All known gardens

    """
    # This is necessary for as long as local_garden is still needed. See the notes
    # there for more detail.
    gardens = db.query(
        Garden, filter_params={"connection_type__ne": "LOCAL", "has_parent": False}
    )

    if include_local:
        gardens += [local_garden()]

    for garden in gardens:
        get_children_garden(garden)

    return gardens


def local_garden(all_systems: bool = False) -> Garden:
    """Get the local garden definition

    Args:
        all_systems: If False, only include "local" systems in the garden systems list

    Returns:
        The local Garden
    """
    # This function is still necessary because there are various things that expect
    # the system information to be embedded in the garden document itself (as opposed
    # Systems just having a reference to their garden). There is nothing that would
    # keep a LOCAL garden's embedded list of systems up to date currently, so we instead
    # build the list of systems (and namespaces) at call time. Once the System
    # relationship has been refactored, the need for this function should go away.
    garden: Garden = db.query_unique(Garden, connection_type="LOCAL")

    filter_params = {}
    if not all_systems:
        filter_params["local"] = True

    garden.systems = get_systems(filter_params=filter_params)
    garden.namespaces = get_namespaces()

    return garden


@publish_event(Events.GARDEN_SYNC)
def publish_garden(status: str = "RUNNING") -> Garden:
    """Get the local garden, publishing a GARDEN_SYNC event

    Args:
        status: The garden status

    Returns:
        The local garden, all systems
    """
    garden = local_garden()
    get_children_garden(garden)
    garden.connection_type = None
    garden.status = status

    return garden


def update_garden_config(garden: Garden) -> Garden:
    """Update Garden configuration parameters

    Args:
        garden: The Garden to Update

    Returns:
        The Garden updated

    """
    db_garden = db.query_unique(Garden, id=garden.id)
    db_garden.connection_params = garden.connection_params
    db_garden.connection_type = garden.connection_type
    db_garden.status = "INITIALIZING"

    return update_garden(db_garden)


def update_garden_receiving_heartbeat(
    api: str, garden_name: str = None, garden: Garden = None
):
    if garden is None:
        garden = db.query_unique(Garden, name=garden_name)

    # if garden doens't exist, create it
    if garden is None:
        garden = create_garden(Garden(name=garden_name, connection_type="Remote"))

    updates = {}

    connection_set = False

    for connection in garden.receiving_connections:
        if connection.api == api:
            connection_set = True
            connection.status_info["heartbeat"] = datetime.utcnow()
            if connection.status != "DISABLED":
                connection.status = "RECEIVING"

    # If the receiving type is unknown, enable it by default and set heartbeat
    if not connection_set:
        connection = Connection(api=api, status="DISABLED")

        # Check if there is a config file
        path = Path(f"{config.get('children.directory')}/{garden.name}.yaml")
        if path.exists():
            garden_config = config.load_child(path)
            if config.get("receiving", config=garden_config):
                connection.status = "RECEIVING"

        connection.status_info["heartbeat"] = datetime.utcnow()
        garden.receiving_connections.append(connection)

    updates["receiving_connections"] = [
        db.from_brewtils(connection) for connection in garden.receiving_connections
    ]

    return db.modify(garden, **updates)


def update_garden_status(garden_name: str, new_status: str) -> Garden:
    """Update an Garden status.

    Will also update the status_info heartbeat.

    Args:
        garden_name: The Garden Name
        new_status: The new status

    Returns:
        The updated Garden
    """
    garden = db.query_unique(Garden, name=garden_name)

    if new_status == "RUNNING":
        for connection in garden.publishing_connections:
            if connection.status == "DISABLED":
                update_garden_publishing(
                    "PUBLISHING",
                    api=connection.api,
                    garden=garden,
                    override_status=False,
                )

        for connection in garden.receiving_connections:
            if connection.status == "DISABLED":
                update_garden_receiving(
                    "RECEIVING",
                    api=connection.api,
                    garden=garden,
                    override_status=False,
                )

    elif new_status == "STOPPED":
        for connection in garden.publishing_connections:
            if connection.status in [
                "PUBLISHING",
                "RECEIVING",
                "UNREACHABLE",
                "UNRESPONSIVE",
                "ERROR",
                "UNKNOWN",
            ]:
                update_garden_publishing(
                    "DISABLED", api=connection.api, garden=garden, override_status=False
                )

        for connection in garden.receiving_connections:
            if connection.status in [
                "PUBLISHING",
                "RECEIVING",
                "UNREACHABLE",
                "UNRESPONSIVE",
                "ERROR",
                "UNKNOWN",
            ]:
                update_garden_receiving(
                    "DISABLED", api=connection.api, garden=garden, override_status=False
                )

    garden.status = new_status
    garden.status_info["heartbeat"] = datetime.utcnow()

    return update_garden(garden)


def remove_remote_users(garden: Garden):
    RemoteUser.objects.filter(garden=garden.name).delete()

    if garden.children:
        for children in garden.children:
            remove_remote_users(children)


def remove_remote_systems(garden: Garden):
    for system in garden.systems:
        remove_system(system.id)

    if garden.children:
        for children in garden.children:
            remove_remote_systems(children)


@publish_event(Events.GARDEN_REMOVED)
def remove_garden(garden_name: str = None, garden: Garden = None) -> None:
    """Remove a garden

    Args:
        garden_name: The Garden name

    Returns:
        The deleted garden
    """

    garden = garden or get_garden(garden_name)

    remove_remote_users(garden)
    remove_remote_systems(garden)

    for child in garden.children:
        remove_garden(child)

    db.delete(garden)

    return garden


@publish_event(Events.GARDEN_CREATED)
def create_garden(garden: Garden) -> Garden:
    """Create a new Garden

    Args:
        garden: The Garden to create

    Returns:
        The created Garden

    """
    if not garden.publishing_connections:
        garden.publishing_connections = [
            Connection(api="HTTP", status="MISSING_CONFIGURATION"),
            Connection(api="STOMP", status="MISSING_CONFIGURATION"),
        ]

    garden.status_info["heartbeat"] = datetime.utcnow()

    return db.create(garden)


def garden_add_system(system: System, garden_name: str) -> Garden:
    """Add a System to a Garden

    Args:
        system: The system to add
        garden_name: The Garden Name to add it to

    Returns:
        The updated Garden

    """
    try:
        garden = get_garden(garden_name)
    except DoesNotExist:
        raise PluginError(
            f"Garden '{garden_name}' does not exist, unable to map '{str(system)}"
        )

    if system.namespace not in garden.namespaces:
        garden.namespaces.append(system.namespace)

    if str(system) not in garden.systems:
        garden.systems.append(str(system))

    return update_garden(garden)


@publish_event(Events.GARDEN_UPDATED)
def update_garden(garden: Garden) -> Garden:
    """Update a Garden

    Args:
        garden: The Garden to update

    Returns:
        The updated Garden
    """

    return db.update(garden)


def upsert_garden(garden: Garden, skip_connections: bool = True) -> Garden:
    """Updates or inserts Garden"""

    if garden.children:
        for child in garden.children:
            upsert_garden(child, skip_connections=False)

    try:
        existing_garden = get_garden(garden.name)

    except DoesNotExist:
        existing_garden = None

    del garden.children

    if existing_garden is None:
        return create_garden(garden)
    else:
        for attr in ("status", "status_info", "namespaces", "systems", "metadata"):
            setattr(existing_garden, attr, getattr(garden, attr))
        if not skip_connections:
            for attr in ("receiving_connections", "publishing_connections"):
                # Drop any config information is passed
                for attribute in getattr(garden, attr):
                    attribute.config = {}
                setattr(existing_garden, attr, getattr(garden, attr))

        return update_garden(existing_garden)


@publish_event(Events.GARDEN_CONFIGURED)
def update_garden_publishing(
    status: str,
    api: str = None,
    garden: Garden = None,
    garden_name: str = None,
    override_status: bool = True,
):
    if not garden:
        garden = db.query_unique(Garden, name=garden_name)

    connection_set = False

    for connection in garden.publishing_connections:
        if api is None or connection.api == api:
            if override_status or connection.status not in [
                "NOT_CONFIGURED",
                "MISSING_CONFIGURATION",
            ]:
                connection.status = status
            connection_set = True

    if not connection_set and api:
        garden.publishing_connections.append(Connection(api=api, status=status))

    return db.update(garden)


@publish_event(Events.GARDEN_CONFIGURED)
def update_garden_receiving(
    status: str,
    api: str = None,
    garden: Garden = None,
    garden_name: str = None,
    override_status: bool = True,
):
    if not garden:
        garden = db.query_unique(Garden, name=garden_name)

    connection_set = False

    if garden.receiving_connections:
        for connection in garden.receiving_connections:
            if api is None or connection.api == api:
                if override_status or connection.status not in [
                    "NOT_CONFIGURED",
                    "MISSING_CONFIGURATION",
                ]:
                    connection.status = status
                connection_set = True

    if not connection_set and api:
        garden.receiving_connections.append(Connection(api=api, status=status))

    return db.update(garden)


def load_garden_connections(garden: Garden):
    path = Path(f"{config.get('children.directory')}/{garden.name}.yaml")

    garden.publishing_connections.clear()

    if not path.exists():
        garden.status = "NOT_CONFIGURED"
        return garden

    try:
        garden_config = config.load_child(path)
    except (
        YapconfItemNotFound,
        YapconfLoadError,
        YapconfSourceError,
        YapconfSpecError,
    ):
        garden.status = "CONFIGURATION_ERROR"
        garden.publishing_connections.append(
            Connection(api="HTTP", status="CONFIGURATION_ERROR")
        )
        garden.publishing_connections.append(
            Connection(api="STOMP", status="CONFIGURATION_ERROR")
        )
        return garden

    if config.get("http.enabled", garden_config):
        config_map = {
            "http.host": "host",
            "http.port": "port",
            "http.ssl.enabled": "ssl",
            "http.url_prefix": "url_prefix",
            "http.ssl.ca_cert": "ca_cert",
            "http.ssl.ca_verify": "ca_verify",
            "http.ssl.client_cert": "client_cert",
            "http.client_timeout": "client_timeout",
            "http.username": "username",
            "http.password": "password",
            "http.access_token": "access_token",
            "http.refresh_token": "refresh_token",
        }

        http_connection = Connection(
            api="HTTP",
            status="PUBLISHING" if garden_config.get("publishing") else "DISABLED",
        )
        http_connection.status_info["heartbeat"] = datetime.utcnow()

        for key in config_map:
            http_connection.config.setdefault(
                config_map[key], config.get(key, garden_config)
            )
        garden.publishing_connections.append(http_connection)
    else:
        garden.publishing_connections.append(
            Connection(api="HTTP", status="NOT_CONFIGURED")
        )

    if config.get("stomp.enabled", garden_config):
        config_map = {
            "stomp.host": "host",
            "stomp.port": "port",
            "stomp.send_destination": "send_destination",
            "stomp.subscribe_destination": "subscribe_destination",
            "stomp.username": "username",
            "stomp.password": "password",
            "stomp.ssl": "ssl",
            "stomp.headers": "headers",
        }

        stomp_connection = Connection(
            api="STOMP",
            status="PUBLISHING" if garden_config.get("publishing") else "DISABLED",
        )
        stomp_connection.status_info["heartbeat"] = datetime.utcnow()

        for key in config_map:
            stomp_connection.config.setdefault(
                config_map[key], config.get(key, garden_config)
            )
        if config.get("stomp.send_destination", garden_config):
            garden.publishing_connections.append(stomp_connection)

        if config.get("stomp.subscribe_destination", garden_config):
            garden.receiving_connections.append(stomp_connection)
    else:
        garden.publishing_connections.append(
            Connection(api="STOMP", status="NOT_CONFIGURED")
        )

    for connection in garden.receiving_connections:
        if config.get("receiving", config=garden_config):
            connection.status = "RECEIVING"
        else:
            connection.status = "DISABLED"

    if config.get("unresponsive_timeout", garden_config) > 0:
        garden.metadata["_unresponsive_timeout"] = config.get(
            "unresponsive_timeout", garden_config
        )
    return garden


@publish_event(Events.GARDEN_CONFIGURED)
def load_garden_config(garden: Garden = None, garden_name: str = None):
    if not garden:
        garden = db.query_unique(Garden, name=garden_name)

    garden = load_garden_connections(garden)

    return db.update(garden)


def rescan():
    if config.get("children.directory"):
        children_directory = Path(config.get("children.directory"))
        if children_directory.exists():
            for path in children_directory.iterdir():
                path_parts = path.parts

                if len(path_parts) == 0:
                    continue
                if path_parts[-1].startswith("."):
                    continue

                if not path_parts[-1].endswith(".yaml"):
                    continue

                if not path.exists():
                    continue
                if path.is_dir():
                    continue

                garden_name = path_parts[-1][:-5]

                garden = db.query_unique(Garden, name=garden_name)

                if garden is None:
                    garden = create_garden(
                        Garden(name=garden_name, connection_type="Remote")
                    )

                # Garden was created by child, update the connection information if available
                for connection in garden.publishing_connections:
                    if connection.status == "MISSING_CONFIGURATION":
                        load_garden_config(garden=garden)
                        garden_sync(garden.name)
                        break


def garden_sync(sync_target: str = None):
    """Do a garden sync

    If we're here it means the Operation.target_garden_name was *this* garden. So the
    sync_target is either *this garden* or None.

    If the former then call the method to publish the current garden.

    If the latter then we need to send sync operations to *all* known downstream
    gardens.

    Args:
        sync_target:

    Returns:

    """
    # If a Garden Name is provided, determine where to route the request
    if sync_target:
        logger.debug("Processing garden sync, about to publish")

        publish_garden()
        publish_command_publishing_blocklist()

    else:
        from beer_garden.router import route

        # Iterate over all gardens and forward the sync requests
        for garden in get_gardens(include_local=False):
            try:
                logger.debug(f"About to create sync operation for garden {garden.name}")

                route(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        target_garden_name=garden.name,
                        kwargs={"sync_target": garden.name},
                    )
                )
            except ForwardException:
                pass


def publish_local_garden():
    local_garden = get_garden(config.get("garden.name"))
    publish(
        Event(
            name=Events.GARDEN_UPDATED.name,
            garden=config.get("garden.name"),
            payload_type="Garden",
            payload=local_garden,
        )
    )


def garden_unresponsive_trigger():
    for garden in get_gardens(include_local=False):
        interval_value = garden.metadata.get(
            "_unresponsive_timeout", config.get("children.unresponsive_timeout")
        )

        if interval_value > 0:
            timeout = datetime.utcnow() - timedelta(minutes=interval_value)

            for connection in garden.receiving_connections:
                if connection.status in ["RECEIVING"]:
                    if connection.status_info["heartbeat"] < timeout:
                        update_garden_receiving(
                            "UNRESPONSIVE", api=connection.api, garden=garden
                        )


def handle_event(event):
    """Handle garden-related events

    For GARDEN events we only care about events originating from downstream. We also
    only care about immediate children, not grandchildren.

    Whenever a garden event is detected we should update that garden's database
    representation.

    This method should NOT update the routing module. Let its handler worry about that!
    """
    if event.garden != config.get("garden.name"):
        if event.name in (
            Events.GARDEN_STARTED.name,
            Events.GARDEN_UPDATED.name,
            Events.GARDEN_STOPPED.name,
            Events.GARDEN_SYNC.name,
        ):
            logger.debug(f"Processing {event.garden} for {event.name}")

            for system in event.payload.systems:
                system.local = False

            # Remove systems that are tracking locally
            remote_systems = []
            for system in event.payload.systems:
                if (
                    len(
                        get_systems(
                            filter_params={
                                "local": True,
                                "namespace": system.namespace,
                                "name": system.name,
                                "version": system.version,
                            }
                        )
                    )
                    < 1
                ):
                    remote_systems.append(system)
            event.payload.systems = remote_systems

            upsert_garden(event.payload)

            # Publish update events for UI to dynamically load changes for Systems
            publish_local_garden()

    elif event.name == Events.GARDEN_UNREACHABLE.name:
        target_garden = get_garden(event.payload.target_garden_name)

        if target_garden.status not in [
            "UNREACHABLE",
            "STOPPED",
            "BLOCKED",
            "ERROR",
        ]:
            update_garden_status(event.payload.target_garden_name, "UNREACHABLE")
    elif event.name == Events.GARDEN_ERROR.name:
        target_garden = get_garden(event.payload.target_garden_name)

        if target_garden.status not in [
            "UNREACHABLE",
            "STOPPED",
            "BLOCKED",
            "ERROR",
        ]:
            update_garden_status(event.payload.target_garden_name, "ERROR")
    elif event.name == Events.GARDEN_NOT_CONFIGURED.name:
        target_garden = get_garden(event.payload.target_garden_name)

        if target_garden.status == "NOT_CONFIGURED":
            update_garden_status(event.payload.target_garden_name, "NOT_CONFIGURED")

    elif event.name == Events.GARDEN_CONFIGURED.name:
        publish_garden()

    if "SYSTEM" in event.name or "INSTANCE" in event.name:
        # If a System or Instance is updated, publish updated Local Garden Model for UI
        publish_local_garden()
