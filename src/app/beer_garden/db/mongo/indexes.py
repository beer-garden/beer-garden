# -*- coding: utf-8 -*-
import logging

from mongoengine.errors import FieldDoesNotExist, InvalidDocumentError
from pymongo import UpdateMany, UpdateOne
from pymongo.errors import OperationFailure

import beer_garden.config as config
from beer_garden.errors import IndexOperationError

logger = logging.getLogger(__name__)


def update_request_ttl_indexes(command_type, ttl, previous_ttl):
    from brewtils.models import Request
    from mongoengine.connection import get_db

    db = get_db()

    request_index = f"{command_type.lower()}_updated_at_index_tt"
    gridfs_index = f"{command_type.lower()}_updated_at_gridfs_index_ttl"
    gridfs_chunk_index = f"{command_type.lower()}_updated_at_gridfs_chunk_index_ttl"
    raw_file_index = f"{command_type.lower()}_updated_at_raw_file_index_ttl"
    file_index = f"{command_type.lower()}_updated_at_file_index_ttl"
    file_chunk_index = f"{command_type.lower()}_updated_at_file_chunk_index_ttl"

    if ttl != previous_ttl or ttl < 0:
        if request_index in db["request"].index_information():
            db["request"].drop_index(request_index)
            logger.warning(f"Dropped old {request_index} index")

        if gridfs_index in db["fs.files"].index_information():
            db["fs.files"].drop_index(gridfs_index)
            logger.warning(f"Dropped old {gridfs_index} index")

        if gridfs_chunk_index in db["fs.chunks"].index_information():
            db["fs.chunks"].drop_index(gridfs_chunk_index)
            logger.warning(f"Dropped old {gridfs_chunk_index} index")

        if raw_file_index in db["raw_file"].index_information():
            db["raw_file"].drop_index(raw_file_index)
            logger.warning(f"Dropped old {raw_file_index} index")

        if file_index in db["file"].index_information():
            db["file"].drop_index(file_index)
            logger.warning(f"Dropped old {file_index} index")

        if file_chunk_index in db["file_chunk"].index_information():
            db["file_chunk"].drop_index(file_chunk_index)
            logger.warning(f"Dropped old {file_chunk_index} index")

    if ttl > -1:
        if request_index not in db["request"].index_information():
            db["request"].create_index(
                [("updated_at", 1)],
                name=request_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )
            logger.warning(f"Created new {request_index} index")

        if gridfs_index not in db["fs.files"].index_information():
            db["fs.files"].create_index(
                [("updated_at", 1)],
                name=gridfs_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )
            logger.warning(f"Created new {gridfs_index} index")

        if gridfs_chunk_index not in db["fs.chunks"].index_information():
            db["fs.chunks"].create_index(
                [("updated_at", 1)],
                name=gridfs_chunk_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )
            logger.warning(f"Created new {gridfs_chunk_index} index")

        if raw_file_index not in db["raw_file"].index_information():
            db["raw_file"].create_index(
                [("updated_at", 1)],
                name=raw_file_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )
            logger.warning(f"Created new {raw_file_index} index")

        if file_index not in db["file"].index_information():
            db["file"].create_index(
                [("updated_at", 1)],
                name=file_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )
            logger.warning(f"Created new {file_index} index")

        if file_chunk_index not in db["file_chunk"].index_information():
            db["file_chunk"].create_index(
                [("updated_at", 1)],
                name=file_chunk_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "root_command_type": command_type,
                    "status": {"$in": Request.COMPLETED_STATUSES},
                },
            )
            logger.warning(f"Created new {file_chunk_index} index")


def update_file_ttl_indexes(ttl, previous_ttl):

    from mongoengine.connection import get_db

    db = get_db()

    file_index = "updated_at_file_index_ttl"
    file_chunk_index = "updated_at_file_chunk_index_ttl"

    if ttl != previous_ttl or ttl < 0:

        if file_index in db["file"].index_information():
            db["file"].drop_index(file_index)
            logger.warning(f"Dropped old {file_index} index")

        if file_chunk_index in db["file_chunk"].index_information():
            db["file_chunk"].drop_index(file_chunk_index)
            logger.warning(f"Dropped old {file_chunk_index} index")

    if ttl > -1:

        if file_index not in db["file"].index_information():
            db["file"].create_index(
                [("updated_at", 1)],
                name=file_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "owner_type": "JOB",
                    "job": None,
                },
            )
            logger.warning(f"Created new {file_index} index")

        if file_chunk_index not in db["file_chunk"].index_information():
            db["file_chunk"].create_index(
                [("updated_at", 1)],
                name=file_chunk_index,
                expireAfterSeconds=ttl * 60,
                partialFilterExpression={
                    "owner": None,
                },
            )
            logger.warning(f"Created new {file_chunk_index} index")


def update_ttl_indexes():
    from mongoengine.connection import get_db

    db = get_db()

    action_ttl = config.get("db.prune.ttl.action", default=-1)
    info_ttl = config.get("db.prune.ttl.info", default=15)
    file_ttl = config.get("db.prune.ttl.file", default=15)

    previous_config = db.get_collection("configuration").find_one()

    if not previous_config:
        previous_config = {}

    # TEMP and ADMIN are given 1 minute TTLs by default
    # This is to ensure that APIs can recall the request
    # before the TTL expires

    update_request_ttl_indexes(
        "ACTION", action_ttl, previous_config.get("action_ttl", -1)
    )
    update_request_ttl_indexes("INFO", info_ttl, previous_config.get("info_ttl", 15))
    update_request_ttl_indexes("TEMP", 1, 1)
    update_request_ttl_indexes("ADMIN", 1, 1)

    update_file_ttl_indexes(file_ttl, previous_config.get("file_ttl", 15))


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
