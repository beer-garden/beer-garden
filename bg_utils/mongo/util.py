# -*- coding: utf-8 -*-
import logging
import os

from mongoengine.errors import DoesNotExist, NotUniqueError
from passlib.apps import custom_app_context

logger = logging.getLogger(__name__)


def verify_db(guest_login_enabled):
    """Do everything necessary to ensure the database is in a 'good' state"""
    from bg_utils.mongo.models import Job, Request, Role, System, Principal

    for doc in (Job, Request, Role, System, Principal):
        _check_indexes(doc)

    _ensure_roles()
    _ensure_users(guest_login_enabled)


def _update_request_parent_field_type():
    """Change GenericReferenceField to ReferenceField"""
    from bg_utils.mongo.models import Request

    raw_collection = Request._get_collection()
    for request in raw_collection.find({"parent._ref": {"$type": "object"}}):
        raw_collection.update_one(
            {"_id": request["_id"]}, {"$set": {"parent": request["parent"]["_ref"]}}
        )


def _update_request_has_parent_model():
    from bg_utils.mongo.models import Request

    raw_collection = Request._get_collection()
    raw_collection.update_many({"parent": None}, {"$set": {"has_parent": False}})
    raw_collection.update_many(
        {"parent": {"$not": {"$eq": None}}}, {"$set": {"has_parent": True}}
    )


def _create_role(role):
    """Create a role if it doesn't already exist"""
    from bg_utils.mongo.models import Role

    try:
        Role.objects.get(name=role.name)
    except DoesNotExist:
        logger.warning("Role %s missing, about to create" % role.name)
        role.save()


def _ensure_roles():
    """Create roles if necessary

    There are certain 'convenience' roles that will be created if this is a new
    install (if no roles currently exist).

    Then there are roles that MUST be present. These will always be created if
    they do not exist.
    """
    from bg_utils.mongo.models import Role

    convenience_roles = [
        Role(
            name="bg-readonly",
            description="Allows only standard read actions",
            permissions=[
                "bg-command-read",
                "bg-event-read",
                "bg-instance-read",
                "bg-job-read",
                "bg-queue-read",
                "bg-request-read",
                "bg-system-read",
            ],
        ),
        Role(
            name="bg-operator",
            description="Standard Beergarden user role",
            permissions=[
                "bg-command-read",
                "bg-event-read",
                "bg-instance-read",
                "bg-job-read",
                "bg-queue-read",
                "bg-request-read",
                "bg-system-read",
                "bg-request-create",
            ],
        ),
    ]

    mandatory_roles = [
        Role(
            name="bg-anonymous",
            description="Special role used for non-authenticated users",
            permissions=[
                "bg-command-read",
                "bg-event-read",
                "bg-instance-read",
                "bg-job-read",
                "bg-queue-read",
                "bg-request-read",
                "bg-system-read",
            ],
        ),
        Role(name="bg-admin", description="Allows all actions", permissions=["bg-all"]),
        Role(
            name="bg-plugin",
            description="Allows actions necessary for plugins to function",
            permissions=[
                "bg-instance-update",
                "bg-job-create",
                "bg-job-update",
                "bg-request-create",
                "bg-request-update",
                "bg-system-create",
                "bg-system-read",
                "bg-system-update",
            ],
        ),
    ]

    # Only create convenience roles if this is a fresh database
    if Role.objects.count() == 0:
        logger.warning("No roles found: creating convenience roles")

        for role in convenience_roles:
            try:
                # Since we have a race potential here catch the case where
                # another process has already created the role
                _create_role(role)
            except NotUniqueError:
                logger.warning("Role %s already exists" % role.name)

    for role in mandatory_roles:
        _create_role(role)


def _should_create_admin():
    from bg_utils.mongo.models import Principal

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


def _ensure_users(guest_login_enabled):
    """Create users if necessary

    There are certain 'convenience' users that will be created if this is a new
    install (if no users currently exist).

    Then there are users that MUST be present. These will always be created if
    they do not exist.
    """
    from bg_utils.mongo.models import Principal, Role

    if _should_create_admin():
        default_password = os.environ.get("BG_DEFAULT_ADMIN_PASSWORD")
        logger.warning("Creating missing admin user...")
        if default_password:
            logger.info(
                'Creating username "admin" with custom password set'
                'in environment variable "BG_DEFAULT_ADMIN_PASSWORD"'
            )
        else:
            logger.info(
                'Creating username "admin" with default password. See '
                "Beer Garden documentation for the value."
            )
            default_password = "password"
        Principal(
            username="admin",
            hash=custom_app_context.hash(default_password),
            roles=[Role.objects.get(name="bg-admin")],
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
                username="anonymous", roles=[Role.objects.get(name="bg-anonymous")]
            ).save()


def _check_indexes(document_class):
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
    from pymongo.errors import OperationFailure
    from mongoengine.connection import get_db
    from bg_utils.mongo.models import Request

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
                "Dropping %s indexes failed, please check the database "
                "configuration",
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
                "%s index rebuild failed, please check the database " "configuration",
                document_class.__name__,
            )
            raise
