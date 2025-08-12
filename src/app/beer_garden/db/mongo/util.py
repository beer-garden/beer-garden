# -*- coding: utf-8 -*-
import logging

from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist, FieldDoesNotExist, InvalidDocumentError
from pymongo import UpdateMany, UpdateOne
from pymongo.errors import OperationFailure

import beer_garden
from beer_garden import config
from beer_garden.errors import IndexOperationError

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


def ensure_v2_to_v3_model_migration():
    """Ensures that the Role model is flatten and Command model is an
    EmbeddedDocument

    In Version 2 and earlier the Role model allowed for nested roles. This caused
    recursive approach to determining Principal permissions. This is changed in
    Version 3 to allow for Roles to add complexity of Namespace restrictions which
    would not work properly with nesting.

    Right now if the check fails this will just drop the Roles and Principle
    collections. Since they'll be recreated anyway this isn't the worst, but
    it would be better if we could seamlessly flatten existing permissions.

    In version 2 and earlier the Command model was a top-level collection. This
    causes organization and performance issues, so in version 3 it was changed to be an
    embedded document of the System model. This ensures that's the case.

    Right now if the check fails this will just drop the Systems, Commands, and
    Instances collections. Since they'll be recreated anyway this isn't the worst, but
    it would be better if we could seamlessly move the existing commands into existing
    Systems.
    """
    from beer_garden.db.mongo.models import Role, System

    try:
        if Role.objects.count() > 0:
            _ = Role.objects()[0]
        if System.objects.count() > 0:
            _ = System.objects()[0]
    except (FieldDoesNotExist, InvalidDocumentError):
        logger.warning(
            "Encountered an error loading Roles or Systems. This is most likely because"
            " the database is using the old (v2) style of storing in the database. To"
            " fix this the roles, principles, systems, instances, and commands"
            " collections will be dropped."
        )

        db = get_db()
        db.drop_collection("principal")
        db.drop_collection("role")
        db.drop_collection("command")
        db.drop_collection("instance")
        db.drop_collection("system")


def contains_field(collection_name, field):
    """Checks if any record in the collection contains the specified field"""
    db = get_db()
    collection = db.get_collection(collection_name)

    if collection.find({field: {"$exists": True}}).count() > 0:
        return True
    return False


def contains_fields(collection_name, fields):
    """Checks if any record in the collection contains one of the specified fields"""
    db = get_db()
    collection = db.get_collection(collection_name)

    filter_criteria = {"$or": [{field: {"$exists": True}}] for field in fields}

    if collection.find(filter_criteria).count() > 0:
        return True
    return False


def missing_field(collection_name, field):
    """Checks if any record in the collection is missing the specified field"""
    db = get_db()
    collection = db.get_collection(collection_name)

    if collection.find({field: {"$exists": False}}).count() > 0:
        return True
    return False


def ensure_v3_24_model_migration():
    """Ensures that the Garden model migration to yaml configs"""

    # Look for 3.23 fields
    if contains_field("garden", "connection_params"):
        import os
        from pathlib import Path

        import yaml

        logger.warning(
            "Encountered an error loading Gardens. This is most likely because"
            " the database is using the old (v3.23 or prior) models. Migration"
            " strategy is to map all records in the Garden collection to yaml"
            " files, then drop the Garden collection to be rebuilt."
        )

        db = get_db()

        garden_collection = db.get_collection("garden")

        if garden_collection.find().count() > 1:
            if not os.path.exists(config.get("children.directory")):
                os.makedirs(config.get("children.directory"))

            for legacy_garden in garden_collection.find():
                if legacy_garden["connection_type"] != "LOCAL":
                    if not Path(
                        f"{config.get('children.directory')}/{legacy_garden['name']}.yaml"
                    ).exists():
                        garden_file_data = {"receiving": False, "publishing": False}

                        if legacy_garden["connection_type"] == "HTTP":
                            garden_file_data["http"] = legacy_garden[
                                "connection_params"
                            ]["http"]
                        if legacy_garden["connection_type"] == "STOMP":
                            garden_file_data["stomp"] = legacy_garden[
                                "connection_params"
                            ]["stomp"]

                        logger.warning(
                            (
                                "Mapping Child Config: "
                                f"{config.get('children.directory')}/{legacy_garden['name']}.yaml"
                            )
                        )
                        with open(
                            f"{config.get('children.directory')}/{legacy_garden['name']}.yaml",
                            "w+",
                        ) as ff:
                            yaml.dump(garden_file_data, ff, allow_unicode=True)

        db.drop_collection("garden")


def ensure_v3_27_model_migration():
    """Ensures that the Role model is consolidated

    In Version 3.26 and earlier the utilized role assignments to determine the
    scope of the Role. In Version 3.27 these scopes were incorporated into the
    Role model.

    Right now if the check fails this will just drop any collection associated
    with User Accounts.  Since they'll be recreated anyway this isn't the worst,
    but it would be better if we could seamlessly flatten existing permissions.

    """

    db = get_db()

    collections = db.collection_names()

    # Look for 3.26 Collections
    for legacy_user_collection in ["remote_role", "role_assignment", "remote_user"]:
        if legacy_user_collection in collections:
            logger.warning(
                "Encountered an error loading Roles or Users or User Tokens. This is most"
                " likely because the database is using the old (v3.26 or prior) models."
                " Migration strategy is to drop the roles, remote_roles, role_assignment,"
                " user, remote_user, and user_token collections. The required collections"
                " will be rebuilt."
            )

            db = get_db()
            db.drop_collection("role")
            db.drop_collection("remote_role")
            db.drop_collection("role_assignment")
            db.drop_collection("user")
            db.drop_collection("remote_user")
            db.drop_collection("user_token")
            db.drop_collection("legacy_role")

            return

    # Look for 3.26 fields
    if (
        contains_field("role", "permissions")
        or contains_field("user", "role_assignments")
        or contains_field("user_token", "user")
    ):
        logger.warning(
            "Encountered an error loading Roles or Users or User Tokens. This is most"
            " likely because the database is using the old (v3.26) style of storing in"
            " the database. To fix this the roles, remote_roles, role_assignment, user,"
            " remote_user, and user_token collections will be dropped."
        )

        db = get_db()
        db.drop_collection("role")
        db.drop_collection("remote_role")
        db.drop_collection("role_assignment")
        db.drop_collection("user")
        db.drop_collection("remote_user")
        db.drop_collection("user_token")
        db.drop_collection("legacy_role")


def ensure_v3_29_model_migration():
    db = get_db()
    batch_size = config.get("db.prune.batch_size", default=-1)
    if missing_field("request", "command_display_name"):
        logger.warning(
            "Command display name was not found in Requests and will be added. This is most"
            " likely because the database is using the old (v3.29) style of storing in"
            " the database."
        )
        request_updates = []
        request_collection = db.get_collection("request")
        for legacy_request in request_collection.find(
            {"command_display_name": {"$exists": False}}
        ):
            if legacy_request:
                legacy_request["command_display_name"] = legacy_request["command"]
                request_updates.append(
                    UpdateOne({"_id": legacy_request["_id"]}, {"$set": legacy_request})
                )
            if batch_size > 0 and len(request_updates) > batch_size:
                request_collection.bulk_write(request_updates, ordered=False)
                request_updates = []
        if len(request_updates) > 0:
            request_collection.bulk_write(request_updates, ordered=False)


def ensure_v3_30_model_migration():
    db = get_db()
    batch_size = config.get("db.prune.batch_size", default=-1)

    if contains_fields("garden", ["status", "status_info", "namespaces"]):
        logger.warning(
            "Status or namespaces was found in Garden and will be removed. This is most"
            " likely because the database is using the old (v3.29) style of storing in"
            " the database."
        )
        garden_updates = []
        garden_collection = db.get_collection("garden")
        for legacy_garden in garden_collection.find():
            garden_updates.append(
                UpdateOne(
                    {"_id": legacy_garden["_id"]},
                    {"$unset": {"status": "", "status_info": "", "namespaces": ""}},
                )
            )
            if batch_size > 0 and len(garden_updates) > batch_size:
                garden_collection.bulk_write(garden_updates, ordered=False)
                garden_updates = []
        if len(garden_updates) > 0:
            garden_collection.bulk_write(garden_updates, ordered=False)

    if missing_field("request", "root_command_type"):
        logger.warning(
            "Root Command Type was not found in Requests and will be added."
            " This is most likely because the database is using the old (v3.29) style of"
            " storing in the database."
        )
        request_collection = db.get_collection("request")
        updates = []
        for legacy_request in request_collection.find(
            {"root_command_type": {"$exists": False}},
            {
                "command_type": 1,
                "_id": 1,
            },
        ):
            if legacy_request:

                root_command_type = getattr(legacy_request, "command_type", "ACTION")

                updates.append(
                    UpdateOne(
                        {"_id": legacy_request["_id"]},
                        {
                            "$set": {
                                "root_command_type": root_command_type,
                            }
                        },
                    )
                )

            if batch_size > 0 and len(updates) > batch_size:
                request_collection.bulk_write(updates, ordered=False)
                logger.warning(
                    f"Migrating root_command_type for {len(updates)} Requests"
                )
                updates = []
        if len(updates) > 0:
            request_collection.bulk_write(updates, ordered=False)
            logger.warning(f"Migrating root_command_type for {len(updates)} Requests")


def ensure_model_migration():
    """Ensures that the database is properly migrated. All migrations ran from this
    single function for easy management"""

    db = get_db()
    previous_config = db.get_collection("configuration").find_one()

    if not previous_config or previous_config.get("version") != str(
        beer_garden.__version__
    ):
        # If the version is not set, or the version is not the same as the current
        # version, run all migrations
        logger.warning(
            "Running database migrations. This may take a while depending on the size of"
            " your database."
        )

        ensure_v2_to_v3_model_migration()
        ensure_v3_24_model_migration()
        ensure_v3_27_model_migration()
        ensure_v3_29_model_migration()
        ensure_v3_30_model_migration()
        # After the 3.30.0 migration, we can start parsing the version to determine
        # which migrations to run

    # This sets the last configuration for future migrations to reference
    reset_last_configuration()


def reset_last_configuration():
    from .models import Configuration

    Configuration.objects().delete()

    # We only want to save certain fields from the config

    configuration = Configuration(
        action_ttl=config.get("db.prune.ttl.action", default=-1),
        info_ttl=config.get("db.prune.ttl.info", default=-1),
        version=str(beer_garden.__version__),
    )
    configuration.save()


def update_request_ttl_indexes(command_type, ttl, previous_ttl=-1):
    from brewtils.models import Request
    from mongoengine.connection import get_db

    db = get_db()

    request_index = f"{command_type.lower()}_created_at_index_tt"
    gridfs_index = f"{command_type.lower()}_created_at_gridfs_index_ttl"
    gridfs_chunk_index = f"{command_type.lower()}_created_at_gridfs_chunk_index_ttl"

    if ttl != previous_ttl or ttl < 0:
        if request_index in db["request"].index_information():
            db["request"].drop_index(request_index)

        if gridfs_index in db["fs.files"].index_information():
            db["fs.files"].drop_index(gridfs_index)

        if gridfs_chunk_index in db["fs.chunks"].index_information():
            db["fs.chunks"].drop_index(gridfs_chunk_index)

    if ttl > -1:
        if request_index not in db["request"].index_information():
            db["request"].create_index(
                [("created_at", 1)],
                name=request_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )

        if gridfs_index not in db["fs.files"].index_information():
            db["fs.files"].create_index(
                [("uploadDate", 1)],
                name=gridfs_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )

        if gridfs_chunk_index not in db["fs.chunks"].index_information():
            db["fs.chunks"].create_index(
                [("uploadDate", 1)],
                name=gridfs_chunk_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )


def update_ttl_indexes():
    from mongoengine.connection import get_db

    db = get_db()

    action_ttl = config.get("db.prune.ttl.action", default=-1)
    info_ttl = config.get("db.prune.ttl.info", default=-1)

    previous_config = db.get_collection("configuration").find_one()

    if not previous_config:
        previous_config = {}

    # TEMP and ADMIN are given 1 minute TTLs by default
    # This is to ensure that APIs can recall the request
    # before the TTL expires

    update_request_ttl_indexes(
        "ACTION", action_ttl, previous_config.get("action_ttl", -1)
    )
    update_request_ttl_indexes("INFO", info_ttl, previous_config.get("info_ttl", -1))
    update_request_ttl_indexes("TEMP", 1)
    update_request_ttl_indexes("ADMIN", 1)


def check_indexes(document_class):
    """Ensures indexes are correct.

    If any indexes are missing they will be created.

    If any of them are 'wrong' (fields have changed, etc.) all the indexes for
    that collection will be dropped and rebuilt.

    Args:
        document_class (Document): The document class

    Returns:
        None

    Raises:
        beergarden.IndexOperationError
    """

    from .models import Request

    try:

        existing = document_class._get_collection().index_information()

        if document_class == Request and "parent_instance_index" in existing:
            raise IndexOperationError("Old Request index found, rebuilding")

        # Build up list of current indexes
        spec_indexes = []
        for spec_index in document_class._meta["indexes"]:
            if isinstance(spec_index, dict):
                spec_indexes.append(spec_index["name"])
            elif isinstance(spec_index, str):
                raise IndexOperationError(
                    f"Index {spec_index} does not have name, must rebuild all indexes"
                )

        # Only check for BG created indexes that end in "_index"
        # This skips manual pruner indexes because they end in "_index_ttl"
        for index, _ in existing.items():
            if index.endswith("_index") and index and index not in spec_indexes:
                logger.warning(
                    "Found extra %s index for %s, about to delete it. This could "
                    "take a while :)",
                    index,
                    document_class.__name__,
                )
                document_class._get_collection().drop_index(index)

        # Add missing indexes
        for spec_index in document_class._meta["indexes"]:
            if isinstance(spec_index, dict):

                if spec_index["name"] not in existing:
                    new_index = {"background": True}
                    for key, value in spec_index.items():
                        if key == "fields":
                            new_index["keys"] = value
                        else:
                            new_index[key] = value

                    logger.warning(
                        "Found missing %s index for %s, about to build it. This could "
                        "take a while :)",
                        spec_index["name"],
                        document_class.__name__,
                    )
                    document_class.create_index(**new_index)

        document_class.ensure_indexes()

    except (IndexOperationError, OperationFailure):
        logger.warning(
            "%s collection indexes verification failed, attempting to rebuild",
            document_class.__name__,
        )

        # Unfortunately mongoengine sucks. The index that failed is only
        # returned as part of the error message. I REALLY don't want to parse
        # an error string to find the index to drop. Also, ME only verifies /
        # creates the indexes in bulk - there's no way to iterate through the
        # index definitions and try them one by one. Since our indexes should be
        # small and built in the background anyway just redo all of them

        try:
            document_class._get_collection().drop_indexes()
            logger.warning("Dropped indexes for %s collection", document_class.__name__)
        except OperationFailure:
            logger.error(
                "Dropping %s indexes failed, please check the database configuration",
                document_class.__name__,
            )
            raise

        if document_class == Request:
            logger.warning(
                "Request definition is potentially out of date. About to check and "
                "update if necessary - this could take several minutes."
            )

            # bg-utils 2.3.3 -> 2.3.4 create the `has_parent` field
            _update_request_has_parent_model()

            # bg-utils 2.4.6 -> 2.4.7 change parent to ReferenceField
            _update_request_parent_field_type()

            logger.warning("Request definition check/update complete.")

        try:
            document_class.ensure_indexes()
            logger.warning("%s indexes rebuilt successfully", document_class.__name__)
        except OperationFailure:
            logger.error(
                "%s index rebuild failed, please check the database configuration",
                document_class.__name__,
            )
            raise

    try:
        if document_class.objects.count() > 0:
            document_class.objects.first()
        logger.info("%s table looks good", document_class.__name__)
    except (FieldDoesNotExist, InvalidDocumentError):
        logger.error(
            (
                "%s table failed to load properly to validate old indexes and "
                "fields, please check the Change Log for any major model changes"
            ),
            document_class.__name__,
        )
        raise


def _update_request_parent_field_type():
    """Change GenericReferenceField to ReferenceField"""
    from .models import Request

    batch_size = config.get("db.prune.batch_size", default=-1)
    updates = []
    raw_collection = Request._get_collection()
    for request in raw_collection.find({"parent._ref": {"$type": "object"}}):
        updates.append(
            UpdateOne(
                {"_id": request["_id"]}, {"$set": {"parent": request["parent"]["_ref"]}}
            )
        )
        if batch_size > 0 and len(updates) > batch_size:
            raw_collection.bulk_write(updates, ordered=False)
            updates = []
    if len(updates) > 0:
        raw_collection.bulk_write(updates, ordered=False)


def _update_request_has_parent_model():
    from .models import Request

    updates = []
    raw_collection = Request._get_collection()
    updates.append(UpdateMany({"parent": None}, {"$set": {"has_parent": False}}))
    updates.append(
        UpdateMany({"parent": {"$not": {"$eq": None}}}, {"$set": {"has_parent": True}})
    )
    raw_collection.bulk_write(updates, ordered=False)


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

    from .models import Garden, System, Topic

    command_hash = []

    for garden in Garden.objects():
        if garden.name == config.get("garden.name"):
            garden.systems = System.objects(local=True)
        for system in garden.systems:
            for instance in system.instances:
                for command in system.commands:
                    command_hash.append(
                        (
                            f"{garden.name}.{system.namespace}.{system.name}."
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
