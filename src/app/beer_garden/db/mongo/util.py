# -*- coding: utf-8 -*-
import logging
import os
from typing import Union

import yaml
from bson import DBRef
from marshmallow.exceptions import ValidationError as SchemaValidationError
from mongoengine.connection import get_db
from mongoengine.errors import (
    DoesNotExist,
    FieldDoesNotExist,
    InvalidDocumentError,
    ValidationError,
)
from passlib.apps import custom_app_context

from beer_garden import config
from beer_garden.errors import ConfigurationError
from beer_garden.role import sync_roles

logger = logging.getLogger(__name__)


def ensure_local_garden():
    """Creates an entry in the database for the local garden

    The local garden info is configured via the configuration file. Internally
    however, it is better to treat local and remote gardens the same in terms of how
    we access them, etc. For that reason, we read the garden info from the configuration
    and create or update the Garden database entry for it.
    """
    from .models import Garden

    try:
        garden = Garden.objects.get(connection_type="LOCAL")
    except DoesNotExist:
        garden = Garden(connection_type="LOCAL", status="RUNNING")

    garden.name = config.get("garden.name")

    garden.save()


def ensure_roles():
    """Create roles if necessary

    If auth.role_definition_file is set in the main application config, this will
    load that file and pass it over to sync_roles to make the Role definitions in the
    database match what is defined in the file.
    """
    role_definition_file: Union[str, None] = config.get("auth.role_definition_file")

    if role_definition_file:
        logger.info(f"Syncing role definitions from {role_definition_file}")

        try:
            with open(role_definition_file, "r") as filestream:
                role_definitions = yaml.safe_load(filestream)
                sync_roles(role_definitions)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Role definition file {role_definition_file} not found."
            )
        except SchemaValidationError:
            raise ConfigurationError(
                f"Error processing role definition file {role_definition_file}."
            )
        except ValidationError as validation_error:
            raise ConfigurationError(
                f"Invalid role definition in {role_definition_file}: "
                f"{validation_error}"
            )
    else:
        logger.info("auth.role_definition_file not defined. No roles will be synced.")


def ensure_users(guest_login_enabled):
    """Create users if necessary

    There are certain 'convenience' users that will be created if this is a new
    install (if no users currently exist).

    Then there are users that MUST be present. These will always be created if
    they do not exist.
    """
    from .models import Principal

    if _should_create_admin():
        default_password = os.environ.get("BG_DEFAULT_ADMIN_PASSWORD")
        logger.warning("Creating missing admin user...")
        if default_password:
            logger.info(
                'Creating username "admin" with custom password set'
                'in environment variable "BG_DEFAULT_ADMIN_PASSWORD"'
            )
        else:
            default_password = "password"
            logger.info(
                'Creating username "admin" with password "%s"' % default_password
            )
        Principal(
            username="admin",
            hash=custom_app_context.hash(default_password),
            roles=[],
            metadata={"auto_change": True, "changed": False},
        ).save()

    try:
        anonymous_user = Principal.objects.get(username="anonymous")

        # Here we specifically check for None because bartender does
        # not have the guest_login_enabled configuration, so we don't
        # really know what to do in that case, so we just allow it to
        # stay around. This actually shouldn't matter anyway, because
        # brew-view is a dependency for bartender to start so brew-view
        # should have already done the right thing anyway.
        if guest_login_enabled is not None and not guest_login_enabled:
            logger.info(
                "Previous anonymous user detected, but the config indicates "
                "guest login is not enabled. Removing old anonymous user."
            )
            anonymous_user.delete()

    except DoesNotExist:
        if guest_login_enabled:
            logger.info("Creating anonymous user.")
            Principal(
                username="anonymous",
                roles=[],
            ).save()


def ensure_owner_collection_migration():
    """We ran into an issue with 3.0.5 where Requests and Jobs got migrated over to
    the Owner collection. This is in place to resolve that."""

    database = get_db()

    if database["owner"].count():
        logger.warning(
            "Found owner collection, migrating documents to appropriate collections. "
            "This could take a while :)"
        )

        for doc in database["owner"].find({"_cls": "Owner.Request"}):
            try:
                del doc["_cls"]

                if doc.get("has_parent"):
                    doc["parent"] = DBRef("request", doc["parent"].id)

                database["request"].insert_one(doc)
            except Exception:
                logger.error(f"Error migrating request {doc['_id']}")

        for doc in database["owner"].find({"_cls": "Owner.Job"}):
            try:
                del doc["_cls"]

                database["job"].insert_one(doc)
            except Exception:
                logger.error(f"Error migrating job {doc['_id']}")

        for doc in database["file"].find():
            try:
                if doc["owner_type"] == "REQUEST":
                    doc["request"] = doc["owner"]
                elif doc["owner_type"] == "JOB":
                    doc["job"] = doc["owner"]
                else:
                    logger.error(f"Unable to migrate file {doc['_id']}: bad owner type")
                    database["file"].delete_one({"_id": doc["_id"]})
                    continue

                doc["owner"] = None

                database["file"].replace_one({"_id": doc["_id"]}, doc)
            except Exception:
                logger.error(f"Error migrating file {doc['_id']}, removing")
                database["file"].delete_one({"_id": doc["_id"]})

        logger.info("Dropping owner collection (this is intended!)")
        database.drop_collection("owner")


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
    from beer_garden.db.mongo.models import LegacyRole, System

    try:
        if LegacyRole.objects.count() > 0:
            _ = LegacyRole.objects()[0]
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
    ensure_owner_collection_migration()


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
        mongoengine.OperationFailure: Unhandled mongo error
    """
    from mongoengine.connection import get_db
    from pymongo.errors import OperationFailure

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
            raise OperationFailure("Old Request index found, rebuilding")

        if len(spec) < len(existing):
            raise OperationFailure("Extra index found, rebuilding")

        if len(spec) > len(existing):
            logger.warning(
                "Found missing %s indexes, about to build them. This could "
                "take a while :)",
                document_class.__name__,
            )

        document_class.ensure_indexes()

    except OperationFailure:
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


def _create_role(role):
    """Create a role if it doesn't already exist"""
    from .models import LegacyRole

    try:
        LegacyRole.objects.get(name=role.name)
    except DoesNotExist:
        logger.warning("Role %s missing, about to create" % role.name)
        role.save()


def _should_create_admin():
    from .models import Principal

    count = Principal.objects.count()

    if count == 0:
        return True

    try:
        Principal.objects.get(username="admin")
        return False
    except DoesNotExist:
        pass

    if count == 1:
        principal = Principal.objects.get()[0]
        return principal.username == "anonymous"

    # By default, if they have created other users that are not just the
    # anonymous users, we assume they do not want to re-create the admin
    # user.
    return False
