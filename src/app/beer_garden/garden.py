# -*- coding: utf-8 -*-
"""Garden Service

The garden service is responsible for:

* Generating local `Garden` record
* Getting `Garden` objects from the database
* Updating `Garden` objects in the database
* Responding to `Garden` sync requests and forwarding request to children
* Handling `Garden` events
"""
import copy
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from brewtils.errors import PluginError
from brewtils.models import (
    Connection,
    Event,
    Events,
    Garden,
    Operation,
    StatusInfo,
    System,
)
from mongoengine import DoesNotExist
from packaging.version import InvalidVersion, parse
from yapconf.exceptions import (
    YapconfItemNotFound,
    YapconfLoadError,
    YapconfSourceError,
    YapconfSpecError,
)

import beer_garden
import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.errors import (
    ForwardException,
    NotFoundException,
    NotUniqueException,
    RoutingRequestException,
)
from beer_garden.events import publish, publish_event
from beer_garden.systems import get_systems, remove_system

logger = logging.getLogger(__name__)


def filter_router_result(garden: Garden) -> Garden:
    """Filter values for API output"""

    filtered_garden = copy.deepcopy(garden)
    config_whitelist = [
        "host",
        "port",
        "url_prefix",
        "send_destination",
        "subscribe_destination",
    ]

    if filtered_garden.publishing_connections:
        for connection in filtered_garden.publishing_connections:
            drop_keys = []
            for key in connection.config:
                if key not in config_whitelist:
                    drop_keys.append(key)
            for key in drop_keys:
                connection.config.pop(key)

    if filtered_garden.receiving_connections:
        for connection in filtered_garden.receiving_connections:
            drop_keys = []
            for key in connection.config:
                if key not in config_whitelist:
                    drop_keys.append(key)
            for key in drop_keys:
                connection.config.pop(key)

    if filtered_garden.children:
        for child in filtered_garden.children:
            filter_router_result(child)
    return filtered_garden


def get_children_garden(garden: Garden, **kwargs) -> Garden:

    if "include_fields" in kwargs and kwargs["include_fields"]:
        for required_field in ["has_parent", "name", "parent"]:
            if required_field not in kwargs["include_fields"]:
                kwargs["include_fields"].append(required_field)

    kwargs["filter_params"] = {}

    if garden.connection_type == "LOCAL":
        kwargs["filter_params"]["connection_type__ne"] = "LOCAL"
        kwargs["filter_params"]["has_parent"] = False

        garden.children = db.query(Garden, **kwargs)
        if garden.children:
            for child in garden.children:
                child.has_parent = True
                child.parent = garden.name

    else:
        kwargs["filter_params"]["parent"] = garden.name
        garden.children = db.query(Garden, **kwargs)

    if garden.children:
        for child in garden.children:
            get_children_garden(child, **kwargs)
    else:
        garden.children = []

    return garden


def get_garden(garden_name: str, **kwargs) -> Garden:
    """Retrieve an individual Garden

    Args:
        garden_name: The name of Garden

    Returns:
        The Garden

    """

    if "include_fields" in kwargs and kwargs["include_fields"]:
        for required_field in ["has_parent", "name", "parent"]:
            if required_field not in kwargs["include_fields"]:
                kwargs["include_fields"].append(required_field)

    if garden_name == config.get("garden.name"):
        gardens = db.query(Garden, **kwargs)
        garden = None
        for db_garden in gardens:
            if db_garden.name == config.get("garden.name"):
                garden = db_garden
            else:
                if not db_garden.has_parent:
                    db_garden.has_parent = True
                    db_garden.parent = config.get("garden.name")

            db_garden.children = [
                child_garden
                for child_garden in gardens
                if child_garden.name != db_garden.name
                and (
                    (child_garden.has_parent and child_garden.parent == db_garden.name)
                    or (
                        not child_garden.has_parent
                        and db_garden.name == config.get("garden.name")
                    )
                )
            ]

        if garden:
            filter_params = {}
            filter_params["local"] = True
            get_system_kwargs = {}

            get_system_kwargs["filter_params"] = {"local": True}

            # Pass system filters to Systems query
            if kwargs:
                for filter, values in kwargs.items():
                    if (
                        values
                        and isinstance(values, (list, set))
                        and filter not in get_system_kwargs
                    ):
                        query_values = []
                        for value in values:
                            if value.startswith("systems__"):
                                query_values.append(value.replace("systems__", "", 1))

                        if query_values:
                            get_system_kwargs[filter] = query_values

            garden.systems = get_systems(**get_system_kwargs)

    else:
        garden = db.query_unique(Garden, name=garden_name, raise_missing=True, **kwargs)
        get_children_garden(garden, **kwargs)

    return garden


def get_gardens(include_local: bool = True, **kwargs) -> List[Garden]:
    """Retrieve list of all Gardens

    Args:
        include_local: Also include the local garden

    Returns:
        All known gardens

    """
    # This is necessary for as long as local_garden is still needed. See the notes
    # there for more detail.
    gardens = []

    if "include_fields" in kwargs and kwargs["include_fields"]:
        for required_field in ["has_parent", "name", "parent"]:
            if required_field not in kwargs["include_fields"]:
                kwargs["include_fields"].append(required_field)

    if include_local:
        gardens = [local_garden(**kwargs)]

    if "filter_params" not in kwargs:
        kwargs["filter_params"] = {}

    kwargs["filter_params"]["connection_type__ne"] = "LOCAL"
    kwargs["filter_params"]["has_parent"] = False

    gardens += db.query(Garden, **kwargs)

    for garden in gardens:
        get_children_garden(garden, **kwargs)

    return gardens


def local_garden(all_systems: bool = False, **kwargs) -> Garden:
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
    # build the list of systems at call time. Once the System
    # relationship has been refactored, the need for this function should go away.

    if "include_fields" in kwargs and kwargs["include_fields"]:
        if "name" not in kwargs["include_fields"]:
            kwargs["include_fields"].append("name")

    garden: Garden = db.query_unique(Garden, connection_type="LOCAL", **kwargs)

    get_system_kwargs = {}

    get_system_kwargs["filter_params"] = {}
    if not all_systems:
        get_system_kwargs["filter_params"]["local"] = True

    # Pass system filters to Systems query
    if kwargs:
        for filter, values in kwargs.items():
            if values and isinstance(values, list) and filter not in get_system_kwargs:
                query_values = []
                for value in values:
                    if value.startswith("systems__"):
                        query_values.append(value.replace("systems__", "", 1))

                if query_values:
                    get_system_kwargs[filter] = query_values

    garden.systems = get_systems(**get_system_kwargs)
    garden.version = beer_garden.__version__

    return garden


@publish_event(Events.GARDEN_SYNC)
def publish_garden() -> Garden:
    """Get the local garden, publishing a GARDEN_SYNC event

    Returns:
        The local garden, all systems
    """
    garden = local_garden()
    get_children_garden(garden)
    garden.connection_type = None

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

    return update_garden(db_garden)


def check_garden_receiving_heartbeat(
    api: str, garden_name: str = None, garden: Garden = None
):
    if garden is None:
        garden = db.query_unique(
            Garden, name=garden_name, include_fields=["receiving_connections"]
        )

    # if garden doens't exist, create it
    if garden is None:
        garden = create_garden(Garden(name=garden_name, connection_type="Remote"))

    connection_set = False

    if garden.receiving_connections:
        for connection in garden.receiving_connections:
            if connection.api == api:
                connection_set = True
                if connection.status not in [
                    "DISABLED",
                    "NOT_CONFIGURED",
                    "MISSING_CONFIGURATION",
                    "CONFIGURATION_ERROR",
                ]:
                    connection.status = "RECEIVING"
                    connection.status_info.set_status_heartbeat(
                        connection.status,
                        max_history=config.get("garden.status_history"),
                    )
    else:
        garden.receiving_connections = []

    # If the receiving type is unknown, enable it by default and set heartbeat
    if not connection_set:
        connection = Connection(api=api, status="DISABLED")

        # Check if there is a config file
        path = Path(f"{config.get('children.directory')}/{garden.name}.yaml")
        if path.exists():
            garden_config = config.load_child(path)
            if config.get("receiving", config=garden_config):
                connection.status = "RECEIVING"

        connection.status_info.set_status_heartbeat(
            connection.status, max_history=config.get("garden.status_history")
        )
        garden.receiving_connections.append(connection)

    return update_receiving_connections(garden)


@publish_event(Events.GARDEN_UPDATED)
def update_receiving_connections(garden: Garden):

    if garden:
        updates = {}

        updates["receiving_connections"] = [
            db.from_brewtils(connection) for connection in garden.receiving_connections
        ]

        return db.modify(garden, **updates)

    return garden


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

    return update_garden(garden)


def remove_remote_systems(garden: Garden):
    for system in garden.systems:
        remove_system(system.id)


@publish_event(Events.GARDEN_REMOVED)
def remove_garden(garden_name: str = None, garden: Garden = None) -> None:
    """Remove a garden

    Args:
        garden_name: The Garden name

    Returns:
        The deleted garden
    """

    garden = garden or get_garden(garden_name)

    for child in garden.children:
        remove_garden(garden=child)

    remove_remote_systems(garden)

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
        for attr in ("systems", "metadata", "version"):
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

    return garden


def load_garden_file(garden: Garden):
    path = Path(f"{config.get('children.directory')}/{garden.name}.yaml")

    http_publishing_connection = Connection(
        api="HTTP", status="CONFIGURATION_ERROR", status_info=StatusInfo()
    )
    http_receiving_connection = Connection(
        api="HTTP", status="CONFIGURATION_ERROR", status_info=StatusInfo()
    )
    stomp_publishing_connection = Connection(
        api="STOMP", status="CONFIGURATION_ERROR", status_info=StatusInfo()
    )
    stomp_receiving_connection = Connection(
        api="STOMP", status="CONFIGURATION_ERROR", status_info=StatusInfo()
    )

    for connection in garden.publishing_connections:
        if connection.api == "HTTP":
            http_publishing_connection.status_info = connection.status_info
        elif connection.api == "STOMP":
            stomp_publishing_connection.status_info = connection.status_info

    for connection in garden.receiving_connections:
        if connection.api == "HTTP":
            http_receiving_connection.status_info = connection.status_info
        elif connection.api == "STOMP":
            stomp_receiving_connection.status_info = connection.status_info

    if not path.exists():
        return garden

    try:
        garden_config = config.load_child(path)
        garden.default_user = config.get("default_user", garden_config)
        garden.shared_users = config.get("shared_users", garden_config)

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

            http_publishing_connection.status = (
                "PUBLISHING" if garden_config.get("publishing") else "DISABLED"
            )

            for key in config_map:
                http_publishing_connection.config.setdefault(
                    config_map[key], config.get(key, garden_config)
                )

        else:
            http_publishing_connection.status = "NOT_CONFIGURED"

        if config.get("stomp.enabled", garden_config):
            config_map = {
                "stomp.host": "host",
                "stomp.port": "port",
                "stomp.send_destination": "send_destination",
                "stomp.subscribe_destination": "subscribe_destination",
                "stomp.username": "username",
                "stomp.password": "password",
                "stomp.ssl": "ssl",
            }

            stomp_publishing_connection.status = (
                "PUBLISHING" if garden_config.get("publishing") else "DISABLED"
            )

            for key in config_map:
                stomp_publishing_connection.config.setdefault(
                    config_map[key], config.get(key, garden_config)
                )

            headers = []
            for header in config.get("stomp.headers", garden_config):
                stomp_header = {}

                header_dict = json.loads(header.replace("'", '"'))

                stomp_header["key"] = header_dict["stomp.headers.key"]
                stomp_header["value"] = header_dict["stomp.headers.value"]

                headers.append(stomp_header)

            stomp_publishing_connection.config.setdefault("headers", headers)

            if not config.get("stomp.send_destination", garden_config):
                stomp_publishing_connection.status = "DISABLED"

            if config.get("stomp.subscribe_destination", garden_config):
                stomp_receiving_connection.status = (
                    "RECEIVING" if garden_config.get("receiving") else "DISABLED"
                )
                stomp_receiving_connection.config = copy.deepcopy(
                    stomp_publishing_connection.config
                )

        else:
            stomp_publishing_connection.status = (
                "NOT_CONFIGURED" if garden_config.get("publishing") else "DISABLED"
            )
            stomp_receiving_connection.status = (
                "NOT_CONFIGURED" if garden_config.get("receiving") else "DISABLED"
            )

        if not garden_config.get("receiving"):
            http_receiving_connection.status = "DISABLED"
        elif config.get("entry.http.enabled"):
            http_receiving_connection.status = "RECEIVING"
        else:
            http_receiving_connection.status = "NOT_CONFIGURED"

    except (
        YapconfItemNotFound,
        YapconfLoadError,
        YapconfSourceError,
        YapconfSpecError,
    ):
        pass
    finally:

        http_publishing_connection.status_info.set_status_heartbeat(
            http_publishing_connection.status,
            max_history=config.get("garden.status_history"),
        )

        stomp_publishing_connection.status_info.set_status_heartbeat(
            stomp_publishing_connection.status,
            max_history=config.get("garden.status_history"),
        )

        stomp_receiving_connection.status_info.set_status_heartbeat(
            stomp_receiving_connection.status,
            max_history=config.get("garden.status_history"),
        )

        garden.publishing_connections = [
            http_publishing_connection,
            stomp_publishing_connection,
        ]

        http_receiving_connection.status_info.set_status_heartbeat(
            http_receiving_connection.status,
            max_history=config.get("garden.status_history"),
        )

        garden.receiving_connections = [
            stomp_receiving_connection,
            http_receiving_connection,
        ]

    return garden


@publish_event(Events.GARDEN_CONFIGURED)
def load_garden_config(garden: Garden = None, garden_name: str = None):
    if not garden:
        garden = db.query_unique(Garden, name=garden_name)

    garden = load_garden_file(garden)

    updates = {}

    updates["publishing_connections"] = []
    for connection in garden.publishing_connections:
        updates["publishing_connections"].append(db.from_brewtils(connection))

    updates["receiving_connections"] = []
    for connection in garden.receiving_connections:
        updates["receiving_connections"].append(db.from_brewtils(connection))

    return db.modify(garden, **updates)


def rescan(sync_gardens: bool = False):
    if config.get("children.directory"):
        loaded_gardens = []
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
                    try:
                        logger.info(f"Loading new configuration file for {garden_name}")
                        garden = Garden(name=garden_name, connection_type="Remote")
                        garden = create_garden(garden)
                    except NotUniqueException:
                        logger.error(
                            f"Write collision occurred when creating {garden_name}"
                        )
                        garden = db.query_unique(Garden, name=garden_name)

                        if garden is None:
                            raise NotFoundException(
                                f"Failure to load {garden_name} after write collision "
                                "occurred"
                            )
                else:
                    logger.info(
                        f"Loading existing configuration file for {garden_name}"
                    )

                load_garden_config(garden=garden)
                # Just need to publish the event for routing logic
                publish(
                    Event(
                        name=Events.GARDEN_UPDATED.name,
                        garden=config.get("garden.name"),
                        payload_type="Garden",
                        payload=garden,
                    )
                )

                loaded_gardens.append(garden.name)
        else:
            logger.error(
                f"Unable to find Children directory: {str(children_directory.resolve())}"
            )

        if sync_gardens:
            for garden_name in loaded_gardens:
                # Need to give the router a second to load the events
                time.sleep(0.5)
                garden_sync(garden_name)


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

    from beer_garden.router import route

    # If a Garden Name is provided, determine where to route the request
    if sync_target:
        if sync_target == config.get("garden.name"):
            logger.info("Processing local garden sync, about to publish")
            publish_garden()
        else:
            try:

                route(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        target_garden_name=sync_target,
                        kwargs={"sync_target": sync_target},
                    )
                )
            except (ForwardException, RoutingRequestException):
                logger.error(
                    f"Failed to forward sync operation to garden {sync_target}"
                )
    else:
        # Iterate over all gardens and forward the sync requests
        for garden in get_gardens(include_local=False):
            try:
                logger.info(f"About to create sync operation for garden {garden.name}")

                route(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        target_garden_name=garden.name,
                        kwargs={"sync_target": garden.name},
                    )
                )
            except (ForwardException, RoutingRequestException):
                logger.error(
                    f"Failed to forward sync operation to garden {garden.name}"
                )

        logger.info("Processing local garden sync, about to publish")
        publish_garden()


def publish_local_garden_to_api():
    local_garden = get_garden(
        config.get("garden.name"),
        exclude_fields=[
            "systems__instances__status_info",
            "receiving_connections__status_info",
            "publishing_connections__status_info",
        ],
    )
    publish(
        Event(
            name=Events.GARDEN_UPDATED.name,
            garden=config.get("garden.name"),
            payload_type="Garden",
            payload=local_garden,
            metadata={"API_ONLY": True},
        )
    )


def garden_unresponsive_trigger():
    for garden in get_gardens(include_local=False):
        try:
            if (
                garden.version is None
                or garden.version == "UNKNOWN"
                or parse(garden.version) < parse("3.25.1")
            ):
                default_value = 60
            else:
                default_value = -1
        except InvalidVersion:
            default_value = 60

        interval_value = garden.metadata.get("_unresponsive_timeout", default_value)

        if interval_value > 0:
            timeout = datetime.now(timezone.utc) - timedelta(minutes=interval_value)

            update_connection = False
            for connection in garden.receiving_connections:
                if connection.status in ["RECEIVING"]:
                    if connection.status_info.heartbeat < timeout:
                        update_garden_receiving(
                            "UNRESPONSIVE", api=connection.api, garden=garden
                        )
                        logger.error(
                            f"{garden.name} Timed out {interval_value} minutes"
                        )
                        update_connection = True
                elif connection.status == "UNRESPONSIVE":
                    logger.info(f"{garden.name} still unresponsive, pushing sync")
                    garden_sync(garden.name)

            if update_connection:
                update_garden(garden)


def handle_event_filter(event):

    if event.payload_type == Garden.__name__:
        if (
            event.garden == config.get("garden.name")
            and hasattr(event, "payload")
            and hasattr(event.payload, "has_parent")
            and event.payload.has_parent
            and hasattr(event.payload, "parent")
            and event.payload.parent != config.get("garden.name")
        ):
            # Do not process 2 hop garden events
            return True

        if event.name == Events.GARDEN_UPDATED.name and event.garden == config.get(
            "garden.name"
        ):
            # Do not reprocess events
            return True

        if (
            event.garden == config.get("garden.name")
            and event.name
            in [
                Events.GARDEN_CONFIGURED.name,
                Events.GARDEN_REMOVED.name,
                Events.GARDEN_CREATED.name,
            ]
            and not config.get("parent.stomp.enabled")
            and not config.get("parent.http.enabled")
        ):
            # No parent to publish to, so we can skip these events
            return True

    return False


def handle_event(event):
    """Handle garden-related events

    For GARDEN events we only care about events originating from downstream. We also
    only care about immediate children, not grandchildren.

    Whenever a garden event is detected we should update that garden's database
    representation.

    This method should NOT update the routing module. Let its handler worry about that!
    """

    if (
        event.garden == config.get("garden.name")
        and event.name == Events.ENTRY_STARTED.name
    ):

        if "entry_point_type" in event.metadata:
            children = db.query(
                Garden,
                filter_params={"connection_type__ne": "LOCAL", "has_parent": False},
                include_fields=["receiving_connections", "name"],
            )

            for child in children:
                for receiving in child.receiving_connections:
                    # Due to HTTP being enabled by default, if STOMP is enabled
                    # duplicate sync events will be published. Since we don't
                    # know how to identify the correct entry point, we have
                    # to just deque unique the event
                    if receiving.api == event.metadata[
                        "entry_point_type"
                    ] and receiving.status not in ["NOT_CONFIGURED", "DISABLED"]:
                        garden_sync(child.name)
                        break

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

            if event.name == Events.GARDEN_SYNC.name:
                logger.info(f"Garden sync event for {event.payload.name}")

                try:
                    # Check if child garden as deleted
                    db_garden = get_garden(event.payload.name)
                    for db_child in db_garden.children:
                        child_deleted = True
                        if event.payload.children:
                            for event_child in event.payload.children:
                                if db_child.name == event_child.name:
                                    child_deleted = False
                                    break
                        if child_deleted:
                            logger.error(
                                f"Unable to find {db_child.name} in Garden sync"
                            )
                            remove_garden(garden=db_child)
                except DoesNotExist:
                    pass

            upsert_garden(event.payload)

    elif event.name in [
        Events.GARDEN_CONFIGURED.name,
        Events.GARDEN_REMOVED.name,
        Events.GARDEN_CREATED.name,
    ]:
        # This publish garden event is to keep parent gardens in sync
        if config.get("parent.stomp.enabled") or config.get("parent.http.enabled"):
            publish_garden()
    elif "GARDEN" in event.name and event.garden != event.payload.name:
        if event.name in (Events.GARDEN_UPDATED.name,):
            # These are generated by the upsert and needed for the Router logic
            return

        logger.error(
            (
                f"{event.name} source garden {event.garden} does "
                f"not match payload garden {event.payload.name}"
            )
        )
