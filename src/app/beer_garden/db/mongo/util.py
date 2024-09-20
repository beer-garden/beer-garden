# -*- coding: utf-8 -*-
import logging

from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist, FieldDoesNotExist, InvalidDocumentError
from pymongo.errors import OperationFailure

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
        garden = Garden(connection_type="LOCAL", status="RUNNING")

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


def ensure_model_migration():
    """Ensures that the database is properly migrated. All migrations ran from this
    single function for easy management"""

    ensure_v2_to_v3_model_migration()


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
    from mongoengine.connection import get_db

    from .models import Request

    try:
        # Building the indexes could take a while so it'd be nice to give some
        # indication of what's happening. This would be perfect but can't use
        # it! It's broken for text indexes!! MongoEngine is awesome!!
        # diff = collection.compare_indexes(); if diff['missing'] is not None...

        # Since we can't ACTUALLY compare the index spec with what already
        # exists without ridiculous effort:
        spec = document_class.list_indexes()
        existing = document_class._get_collection().index_information()

        if document_class == Request and "parent_instance_index" in existing:
            raise IndexOperationError("Old Request index found, rebuilding")

        if len(spec) < len(existing):
            raise IndexOperationError("Extra index found, rebuilding")

        if len(spec) > len(existing):
            logger.warning(
                "Found missing %s indexes, about to build them. This could "
                "take a while :)",
                document_class.__name__,
            )

        document_class.ensure_indexes()

    except IndexOperationError:
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
            db = get_db()
            db[document_class.__name__.lower()].drop_indexes()
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

    raw_collection = Request._get_collection()
    for request in raw_collection.find({"parent._ref": {"$type": "object"}}):
        raw_collection.update_one(
            {"_id": request["_id"]}, {"$set": {"parent": request["parent"]["_ref"]}}
        )


def _update_request_has_parent_model():
    from .models import Request

    raw_collection = Request._get_collection()
    raw_collection.update_many({"parent": None}, {"$set": {"has_parent": False}})
    raw_collection.update_many(
        {"parent": {"$not": {"$eq": None}}}, {"$set": {"has_parent": True}}
    )
