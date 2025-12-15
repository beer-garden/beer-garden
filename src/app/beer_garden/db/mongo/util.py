# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events
from brewtils.models import Request as BrewtilsRequest
from mongoengine.connection import get_connection
from mongoengine.errors import DoesNotExist
from packaging.version import Version

import beer_garden
import beer_garden.config as config
from beer_garden.db.mongo.models import File, FileChunk, Request

logger = logging.getLogger(__name__)


def ensure_local_garden():
    """Creates an entry in the database for the local garden

    The local garden info is configured via the configuration file. Internally
    however, it is better to treat local and remote gardens the same in terms of how
    we access them, etc. For that reason, we read the garden info from the configuration
    and create or update the Garden database entry for it.
    """
    from .models import Connection, Garden

    try:
        garden = Garden.objects.get(connection_type="LOCAL")
    except DoesNotExist:
        garden = Garden(connection_type="LOCAL")

    garden.name = config.get("garden.name")

    if config.get("parent.sync_interval") > 0:
        garden.metadata["_unresponsive_timeout"] = (
            config.get("parent.sync_interval") * 3
        )
    elif garden.metadata:
        garden.metadata.pop("_unresponsive_timeout", None)

    garden.publishing_connections = []

    if config.get("parent.http.enabled"):
        config_map = {
            "parent.http.host": "host",
            "parent.http.port": "port",
            "parent.http.ssl.enabled": "ssl",
            "parent.http.url_prefix": "url_prefix",
            "parent.http.ssl.ca_cert": "ca_cert",
            "parent.http.ssl.ca_verify": "ca_verify",
            "parent.http.ssl.client_cert": "client_cert",
            "parent.http.client_timeout": "client_timeout",
            "parent.http.username": "username",
            "parent.http.password": "password",
            "parent.http.access_token": "access_token",
            "parent.http.refresh_token": "refresh_token",
        }

        http_connection = Connection(api="HTTP", status="PUBLISHING")

        for key in config_map:
            http_connection.config.setdefault(config_map[key], config.get(key))
        garden.publishing_connections.append(http_connection)

    if config.get("parent.stomp.enabled") and config.get(
        "parent.stomp.send_destination"
    ):
        config_map = {
            "parent.stomp.host": "host",
            "parent.stomp.port": "port",
            "parent.stomp.send_destination": "send_destination",
            "parent.stomp.subscribe_destination": "subscribe_destination",
            "parent.stomp.username": "username",
            "parent.stomp.password": "password",
            "parent.stomp.ssl": "ssl",
            "parent.stomp.headers": "headers",
        }

        stomp_connection = Connection(api="STOMP", status="PUBLISHING")

        for key in config_map:
            stomp_connection.config.setdefault(config_map[key], config.get(key))
        garden.publishing_connections.append(stomp_connection)

    garden.version = beer_garden.__version__

    garden.save()


def is_legacy_mongodb():
    mongo_version = get_connection().server_info().get("version", "0.0.0")
    # # Supports MongoGB 6.0+
    return Version(mongo_version) < Version("7.0.0")


def reset_last_configuration():
    from .models import Configuration

    Configuration.objects().delete()

    # We only want to save certain fields from the config

    configuration = Configuration(
        action_ttl=config.get("db.prune.ttl.action", default=-1),
        info_ttl=config.get("db.prune.ttl.info", default=15),
        file_ttl=config.get("db.prune.ttl.file", default=15),
        version=str(beer_garden.__version__),
    )
    configuration.save()


def prune_topics():
    """
    Prune topics by removing invalid subscribers and deleting topics with no valid
    subscribers.

    This function iterates over all topics and checks each subscriber's validity based
    on their type and existence in the 'system' and 'garden' collections in the database.
    Subscribers of type 'GENERATED' or 'ANNOTATED' are validated against the 'garden'
    and 'system' collections. If a topic has no valid subscribers, it is deleted.
    Otherwise, the topic's subscribers are updated to include only valid subscribers.

    Returns:
        None
    """

    from .models import System, Topic

    command_hash = []

    for system in System.objects().only(
        "garden_name",
        "name",
        "namespace",
        "version",
        "instances.name",
        "commands.name",
    ):

        for instance in system.instances:
            for command in system.commands:
                command_hash.append(
                    (
                        f"{system.garden_name}.{system.namespace}.{system.name}."
                        f"{system.version}.{instance.name}.{command.name}"
                    )
                )

    deleted_topic_count = 0
    deleted_subscriber_count = 0
    for topic in Topic.objects():

        valid_subscribers = []
        for subscriber in topic.subscribers:
            if subscriber.subscriber_type in ["GENERATED", "ANNOTATED"]:
                if (
                    f"{subscriber.garden}.{subscriber.namespace}.{subscriber.system}."
                    f"{subscriber.version}.{subscriber.instance}.{subscriber.command}"
                ) in command_hash:
                    valid_subscribers.append(subscriber)

            else:
                valid_subscribers.append(subscriber)

        if len(topic.subscribers) > 0 and len(valid_subscribers) == 0:
            topic.delete()
            deleted_topic_count = deleted_topic_count + 1
        elif len(valid_subscribers) != len(topic.subscribers):
            topic.subscribers = valid_subscribers
            topic.save()
            deleted_subscriber_count = deleted_subscriber_count + 1

    return deleted_topic_count, deleted_subscriber_count


def unassign_files():
    # Pruning Orphaned Files that think they are associated with a Request or Job
    # but the Request or Job no longer exists in the database

    job_pipeline = [
        {
            "$match": {
                "owner_type": "JOB",
                "job": {"$ne": None},
            }
        },
        {
            "$lookup": {
                "from": "job",
                "localField": "job",
                "foreignField": "_id",
                "as": "lookup_result",
            }
        },
        {"$match": {"lookup_result": {"$size": 0}}},
        {"$project": {"_id": 1}},
    ]

    file_ids = []
    file_ids_str = []

    for doc in File._get_collection().aggregate(job_pipeline):
        file_ids.append(doc["_id"])
        file_ids_str.append(str(doc["_id"]))

    if len(file_ids) > 0:
        batch_size = config.get("db.prune.batch_size")

        if batch_size > 0:
            for i in range(0, len(file_ids), batch_size):
                File._get_collection().update_many(
                    {"_id": {"$in": file_ids[i : i + batch_size]}},
                    {
                        "$unset": {
                            "job": "",
                            "request": "",
                            "owner_id": "",
                            "owner_type": "",
                        }
                    },
                )

                # Legacy code needs the owner field set to properly prune
                if not is_legacy_mongodb():
                    FileChunk._get_collection().update_many(
                        {"file_id": {"$in": file_ids_str[i : i + batch_size]}},
                        {"$unset": {"owner": ""}},
                    )
        else:
            File._get_collection().update_many(
                {"_id": {"$in": file_ids}},
                {
                    "$unset": {
                        "job": "",
                        "request": "",
                        "owner_id": "",
                        "owner_type": "",
                    }
                },
            )

            # Legacy code needs the owner field set to properly prune
            if not is_legacy_mongodb():
                FileChunk._get_collection().update_many(
                    {"file_id": {"$in": file_ids_str}}, {"$unset": {"owner": ""}}
                )
        logger.error(f"{len(file_ids)} Files unassigned owners")
    else:
        logger.debug("No missed owners for Files")


def cancel_local_outstanding():
    """
    Helper function for run to mark requests still outstanding after a certain
    amount of time as canceled.

    Update the newest requests first to give the oldest a chance to finish before
    being canceled.
    """

    prune_config = config.get("db.prune")
    cancel_threshold = prune_config.get("in_progress_request_expiration")
    if cancel_threshold > 0:
        timeout = datetime.now(timezone.utc) - timedelta(minutes=cancel_threshold)

        outstanding_requests = Request.objects.filter(
            status__in=["IN_PROGRESS", "CREATED"],
            updated_at__lte=timeout,
            target_garden=config.get("garden.name"),
        ).order_by("-updated_at")

        cancel_outstanding_requests(outstanding_requests)


# Can be used to cancel outstanding requests for any query
def cancel_outstanding_requests(outstanding_requests):
    from beer_garden.events import publish

    counter = 0
    try:
        for request in outstanding_requests:
            try:
                request.status = "CANCELED"
                request.status_updated_at = datetime.now(timezone.utc)
                request.save()

                publish(
                    Event(
                        name=Events.REQUEST_CANCELED.name,
                        payload_type="Request",
                        payload=BrewtilsRequest(
                            id=request.id,
                            status=request.status,
                            status_updated_at=request.status_updated_at,
                            metadata=request.metadata,
                            target_garden=request.target_garden,
                        ),
                        metadata={"UI_RELOAD": True},
                    )
                )
                counter = counter + 1
            except ModelValidationError:
                # If the Request was already cancelled or completed, then skip cancelling it
                logger.error(
                    f"ModelValidationError: Failed to update outstanding Request {request.id}"
                )
            except DoesNotExist:
                # If the Request was already deleted, then skip cancelling it
                logger.error(
                    (
                        f"DoesNotExist: Attempted to update outstanding request {request.id} "
                        "but does not exist in database"
                    )
                )

    finally:

        if counter > 0:
            logger.error(f"{counter} outstanding Requests cancelled")

        else:
            logger.debug("No outstanding Requests cancelled")
