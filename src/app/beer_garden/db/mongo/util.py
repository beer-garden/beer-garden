# -*- coding: utf-8 -*-
import logging
from typing import Union

import yaml
from marshmallow.exceptions import ValidationError as SchemaValidationError
from mongoengine.connection import get_db
from mongoengine.errors import (
    DoesNotExist,
    FieldDoesNotExist,
    InvalidDocumentError,
    ValidationError,
)
from pymongo.errors import OperationFailure

from beer_garden import config
from beer_garden.api.authorization import Permissions
from beer_garden.db.mongo.models import Role, RoleAssignment, User
from beer_garden.errors import ConfigurationError, IndexOperationError
from beer_garden.role import sync_roles

logger = logging.getLogger(__name__)

PLUGIN_ROLE_PERMISSIONS = [
    Permissions.GARDEN_READ.value,
    Permissions.INSTANCE_READ.value,
    Permissions.INSTANCE_UPDATE.value,
    Permissions.REQUEST_CREATE.value,
    Permissions.REQUEST_READ.value,
    Permissions.REQUEST_UPDATE.value,
    Permissions.SYSTEM_CREATE.value,
    Permissions.SYSTEM_READ.value,
    Permissions.SYSTEM_UPDATE.value,
]


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
    """Create roles if necessary"""
    _configure_superuser_role()
    _configure_plugin_role()
    _sync_roles_from_role_definition_file()


def _sync_roles_from_role_definition_file():
    """If auth.role_definition_file is set in the main application config, this will
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
                f"Invalid role definition in {role_definition_file}: {validation_error}"
            )
    else:
        logger.info("auth.role_definition_file not defined. No roles will be synced.")


def _configure_superuser_role():
    """Creates or updates the superuser role as needed"""
    try:
        superuser = Role.objects.get(name="superuser")
    except Role.DoesNotExist:
        logger.info("Creating superuser role with all permissions")
        superuser = Role(name="superuser")

    superuser.permissions = [permission.value for permission in Permissions]
    superuser.description = "Role containing all permissions"
    superuser.protected = True

    superuser.save()


def _configure_plugin_role():
    """Creates or updates the plugin role as needed"""
    try:
        plugin_role = Role.objects.get(name="plugin")
    except Role.DoesNotExist:
        logger.info("Creating plugin role with select permissions")
        plugin_role = Role(name="plugin")

    plugin_role.permissions = PLUGIN_ROLE_PERMISSIONS
    plugin_role.description = "Role containing plugin permissions"
    plugin_role.protected = True

    plugin_role.save()


def ensure_users():
    """Create user accounts if necessary"""
    if User.objects.count() == 0:
        _create_admin()
        _create_plugin_user()


def _create_admin():
    """Create the default admin user if necessary"""
    username = config.get("auth.default_admin.username")
    password = config.get("auth.default_admin.password")
    superuser_role = Role.objects.get(name="superuser")

    logger.info("Creating default admin user with username: %s", username)

    admin = User(username=username)
    admin.set_password(password)
    admin.role_assignments = [
        RoleAssignment(role=superuser_role, domain={"scope": "Global"})
    ]
    admin.save()


def _create_plugin_user():
    """Create the default user to run Plugins if necessary"""
    username = config.get("plugin.local.auth.username")
    plugin_user = User.objects(username=username).first()

    # Sanity check to make sure we don't accidentally create two
    # users with the same name
    if not plugin_user:
        password = config.get("plugin.local.auth.password")
        plugin_user_role = Role.objects.get(name="plugin")

        logger.info("Creating default plugin user with username: %s", username)

        plugin_user = User(username=username)
        plugin_user.set_password(password)
        plugin_user.role_assignments = [
            RoleAssignment(role=plugin_user_role, domain={"scope": "Global"})
        ]
        plugin_user.save()


def ensure_trigger_migration():
    """File Triggers didn't work all the time, they were removed in 3.14.
    Remove any file trigger jobs."""

    database = get_db()

    for doc in database["job"].find():
        try:
            if doc["trigger_type"] == "file":
                database["job"].delete_one({"_id": doc["_id"]})

        except Exception:
            logger.error(f"Error deleting file trigger {doc['_id']}")


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
    ensure_trigger_migration()


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
