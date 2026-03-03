# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timezone

from mongoengine.connection import get_db
from mongoengine.errors import FieldDoesNotExist, InvalidDocumentError
from packaging.version import Version
from pymongo import UpdateOne
from pymongo.errors import PyMongoError

import beer_garden
import beer_garden.config as config

logger = logging.getLogger(__name__)


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

    if collection.count_documents({field: {"$exists": True}}) > 0:
        return True
    return False


def contains_fields(collection_name, fields):
    """Checks if any record in the collection contains one of the specified fields"""
    db = get_db()
    collection = db.get_collection(collection_name)

    filter_criteria = {"$or": [{field: {"$exists": True}} for field in fields]}

    if collection.count_documents(filter_criteria) > 0:
        return True
    return False


def missing_field(collection_name, field):
    """Checks if any record in the collection is missing the specified field"""
    db = get_db()
    collection = db.get_collection(collection_name)

    if collection.count_documents({field: {"$exists": False}}) > 0:
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

        if garden_collection.count_documents({}) > 1:
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

    collections = db.list_collection_names()

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


def find_root_command_type(request):
    command_type = getattr(request, "command_type", "ACTION")
    if ("has_parent" in request and request["has_parent"]) or (
        "parent" in request and request["parent"] is not None
    ):
        try:
            parent = (
                get_db()
                .get_collection("request")
                .find_one(
                    {"_id": request["parent"].id},
                    {
                        "has_parent": 1,
                        "parent": 1,
                        "command_type": 1,
                        "_id": 1,
                    },
                )
            )
            if parent:
                return find_root_command_type(parent)
        except PyMongoError:
            # if any exception is thrown, just return what we currently have
            pass

    return command_type


def ensure_v3_30_model_migration():
    db = get_db()
    batch_size = config.get("db.prune.batch_size", default=-1)

    request_collection = db.get_collection("request")

    # Migration to ensure source_garden and target_garden are set
    # for new cancellation logic
    request_collection.update_many(
        {"source_garden": {"$exists": False}},
        {"$set": {"source_garden": config.get("garden.name")}},
    )

    request_collection.update_many(
        {"target_garden": {"$exists": False}},
        {"$set": {"target_garden": config.get("garden.name")}},
    )

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

        updates = []
        for legacy_request in request_collection.find(
            {"root_command_type": {"$exists": False}},
            {
                "has_parent": 1,
                "parent": 1,
                "command_type": 1,
                "_id": 1,
            },
        ):
            if legacy_request:

                root_command_type = find_root_command_type(legacy_request)

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

    if missing_field("file", "root_command_type"):
        logger.warning(
            "Root Command Type was not found in File/File Chunk and will be added."
            " This is most likely because the database is using the old (v3.29) style of"
            " storing in the database."
        )

        file_collection = db.get_collection("file")
        file_chunk_collection = db.get_collection("file_chunk")
        file_updates = []
        file_chunk_updates = []
        for legacy_file in file_collection.find(
            {
                "root_command_type": {
                    "$exists": False,
                },
                "owner_type": "REQUEST",
                "request": {"$ne": None},
            },
            {
                "request": 1,
                "_id": 1,
            },
        ):
            if legacy_file:

                file_request = db.get_collection("request").find_one(
                    {"_id": legacy_file["request"]},
                    {"root_command_type": 1, "updated_at": 1, "status": 1},
                )

                if not file_request:
                    file_request = {
                        "root_command_type": "TEMP",
                        "status": "ERROR",
                        "updated_at": datetime.now(timezone.utc),
                    }

                file_updates.append(
                    UpdateOne(
                        {"_id": legacy_file["_id"]},
                        {
                            "$set": {
                                "root_command_type": file_request["root_command_type"],
                                "updated_at": file_request["updated_at"],
                                "status": file_request["status"],
                            }
                        },
                    )
                )

                file_chunk_updates.append(
                    UpdateOne(
                        {"file_id": str(legacy_file["_id"])},
                        {
                            "$set": {
                                "root_command_type": file_request["root_command_type"],
                                "updated_at": file_request["updated_at"],
                                "status": file_request["status"],
                            }
                        },
                    )
                )

            if batch_size > 0 and len(file_updates) > batch_size:
                file_collection.bulk_write(file_updates, ordered=False)
                file_chunk_collection.bulk_write(file_chunk_updates, ordered=False)
                logger.warning(
                    f"Migrating root_command_type for {len(file_updates)} File/File Chunk"
                )
                file_updates = []
                file_chunk_updates = []

        if len(file_updates) > 0:
            file_collection.bulk_write(file_updates, ordered=False)
            file_chunk_collection.bulk_write(file_chunk_updates, ordered=False)
            logger.warning(
                f"Migrating root_command_type for {len(file_updates)} File/File Chunk"
            )
            file_updates = []
            file_chunk_updates = []

    if missing_field("raw_file", "root_command_type"):
        logger.warning(
            "Root Command Type was not found in File/File Chunk and will be added."
            " This is most likely because the database is using the old (v3.29) style of"
            " storing in the database."
        )

        raw_file_collection = db.get_collection("raw_file")
        grid_fs_files_collection = db.get_collection("fs.files")
        grid_fs_chunks_collection = db.get_collection("fs.chunks")

        raw_file_updates = []
        gridfs_updates = []
        gridfs_chunk_updates = []
        for legacy_raw_file in raw_file_collection.find(
            {
                "root_command_type": {
                    "$exists": False,
                },
                "request": {"$ne": None},
            },
            {
                "request": 1,
                "_id": 1,
                "file": 1,
            },
        ):
            if legacy_raw_file:

                raw_file_request = db.get_collection("request").find_one(
                    {"_id": legacy_raw_file["request"]},
                    {"root_command_type": 1, "updated_at": 1, "status": 1},
                )

                if not raw_file_request:
                    raw_file_request = {
                        "root_command_type": "TEMP",
                        "status": "ERROR",
                        "updated_at": datetime.now(timezone.utc),
                    }

                raw_file_updates.append(
                    UpdateOne(
                        {"_id": legacy_raw_file["_id"]},
                        {
                            "$set": {
                                "root_command_type": raw_file_request[
                                    "root_command_type"
                                ],
                                "updated_at": raw_file_request["updated_at"],
                                "status": raw_file_request["status"],
                            }
                        },
                    )
                )

                gridfs_updates.append(
                    UpdateOne(
                        {"_id": legacy_raw_file["file"]},
                        {
                            "$set": {
                                "root_command_type": raw_file_request[
                                    "root_command_type"
                                ],
                                "updated_at": raw_file_request["updated_at"],
                                "status": raw_file_request["status"],
                            }
                        },
                    )
                )

                gridfs_chunk_updates.append(
                    UpdateOne(
                        {"files_id": legacy_raw_file["file"]},
                        {
                            "$set": {
                                "root_command_type": raw_file_request[
                                    "root_command_type"
                                ],
                                "updated_at": raw_file_request["updated_at"],
                                "status": raw_file_request["status"],
                            }
                        },
                    )
                )

            if batch_size > 0 and len(raw_file_updates) > batch_size:
                raw_file_collection.bulk_write(raw_file_updates, ordered=False)
                logger.warning(
                    f"Migrating TTL fields for {len(raw_file_updates)} Raw Files"
                )
                raw_file_updates = []

            if batch_size > 0 and len(gridfs_updates) > batch_size:
                grid_fs_files_collection.bulk_write(gridfs_updates, ordered=False)
                logger.warning(
                    f"Migrating TTL fields for {len(gridfs_updates)} Grid FS files"
                )
                gridfs_updates = []

            if batch_size > 0 and len(gridfs_chunk_updates) > batch_size:
                grid_fs_chunks_collection.bulk_write(
                    gridfs_chunk_updates, ordered=False
                )
                logger.warning(
                    f"Migrating TTL fields for {len(gridfs_chunk_updates)} Grid FS chunks"
                )
                gridfs_chunk_updates = []

        if len(raw_file_updates) > 0:
            raw_file_collection.bulk_write(raw_file_updates, ordered=False)
            logger.warning(
                f"Migrating TTL fields for {len(raw_file_updates)} Raw Files"
            )
            raw_file_updates = []

        if len(gridfs_updates) > 0:
            grid_fs_files_collection.bulk_write(gridfs_updates, ordered=False)
            logger.warning(
                f"Migrating TTL fields for {len(gridfs_updates)} Grid FS files"
            )
            gridfs_updates = []

        if len(gridfs_chunk_updates) > 0:
            grid_fs_chunks_collection.bulk_write(gridfs_chunk_updates, ordered=False)
            logger.warning(
                f"Migrating TTL fields for {len(gridfs_chunk_updates)} Grid FS chunks"
            )
            gridfs_chunk_updates = []

    if missing_field("fs.files", "root_command_type"):

        logger.warning(
            "Root Command Type was not found in GridFS and will be added."
            " This is most likely because the database is using the old (v3.29) style of"
            " storing in the database."
        )

        grid_fs_files_collection = db.get_collection("fs.files")
        grid_fs_chunks_collection = db.get_collection("fs.chunks")

        gridfs_updates = []
        gridfs_chunk_updates = []

        for legacy_request in request_collection.find(
            {
                "$or": [
                    {"output_gridfs": {"$ne": None}},
                    {"parameters_gridfs": {"$ne": None}},
                ]
            },
            {
                "root_command_type": 1,
                "updated_at": 1,
                "status": 1,
                "output_gridfs": 1,
                "parameters_gridfs": 1,
            },
        ):
            if legacy_request:

                if legacy_request.get("output_gridfs"):
                    gridfs_updates.append(
                        UpdateOne(
                            {"_id": legacy_request["output_gridfs"]},
                            {
                                "$set": {
                                    "root_command_type": legacy_request.get(
                                        "root_command_type"
                                    ),
                                    "updated_at": legacy_request.get("updated_at"),
                                    "status": legacy_request.get("status"),
                                }
                            },
                        )
                    )

                    gridfs_chunk_updates.append(
                        UpdateOne(
                            {"files_id": legacy_request["output_gridfs"]},
                            {
                                "$set": {
                                    "root_command_type": legacy_request.get(
                                        "root_command_type"
                                    ),
                                    "updated_at": legacy_request.get("updated_at"),
                                    "status": legacy_request.get("status"),
                                }
                            },
                        )
                    )

                if legacy_request.get("parameters_gridfs"):
                    gridfs_updates.append(
                        UpdateOne(
                            {"_id": legacy_request["parameters_gridfs"]},
                            {
                                "$set": {
                                    "root_command_type": legacy_request.get(
                                        "root_command_type"
                                    ),
                                    "updated_at": legacy_request.get("updated_at"),
                                    "status": legacy_request.get("status"),
                                }
                            },
                        )
                    )

                    gridfs_chunk_updates.append(
                        UpdateOne(
                            {"files_id": legacy_request["parameters_gridfs"]},
                            {
                                "$set": {
                                    "root_command_type": legacy_request.get(
                                        "root_command_type"
                                    ),
                                    "updated_at": legacy_request.get("updated_at"),
                                    "status": legacy_request.get("status"),
                                }
                            },
                        )
                    )

            if batch_size > 0 and len(gridfs_updates) > batch_size:
                grid_fs_files_collection.bulk_write(gridfs_updates, ordered=False)
                logger.warning(
                    f"Migrating TTL fields for {len(gridfs_updates)} Grid FS files"
                )
                gridfs_updates = []

            if batch_size > 0 and len(gridfs_chunk_updates) > batch_size:
                grid_fs_chunks_collection.bulk_write(
                    gridfs_chunk_updates, ordered=False
                )
                logger.warning(
                    f"Migrating TTL fields for {len(gridfs_chunk_updates)} Grid FS chunks"
                )
                gridfs_chunk_updates = []

        if len(gridfs_updates) > 0:
            grid_fs_files_collection.bulk_write(gridfs_updates, ordered=False)
            logger.warning(
                f"Migrating TTL fields for {len(gridfs_updates)} Grid FS files"
            )
            gridfs_updates = []

        if len(gridfs_chunk_updates) > 0:
            grid_fs_chunks_collection.bulk_write(gridfs_chunk_updates, ordered=False)
            logger.warning(
                f"Migrating TTL fields for {len(gridfs_chunk_updates)} Grid FS chunks"
            )
            gridfs_chunk_updates = []

    if missing_field("system", "garden_name"):
        logger.warning(
            "Garden Name was not found in Systems and will be added."
            " This is most likely because the database is using the old (v3.29) style of"
            " storing in the database."
        )

        system_collection = db.get_collection("system")
        garden_collection = db.get_collection("garden")

        updates = []
        for legacy_system in system_collection.find(
            {"garden_name": {"$exists": False}, "local": True},
            {
                "_id": 1,
            },
        ):
            if legacy_system:

                updates.append(
                    UpdateOne(
                        {"_id": legacy_system["_id"]},
                        {
                            "$set": {
                                "garden_name": config.get("garden.name"),
                            }
                        },
                    )
                )

        # If we roll all local systems on the local Garden model, then this
        # is the only migration we need for this
        for garden in garden_collection.find({}, {"name": 1, "systems": 1}):
            for legacy_system in garden["systems"]:
                updates.append(
                    UpdateOne(
                        {"_id": legacy_system},
                        {
                            "$set": {
                                "garden_name": garden["name"],
                            }
                        },
                    )
                )

        if len(updates) > 0:
            system_collection.bulk_write(updates, ordered=False)
            logger.warning(f"Migrating garden_name for {len(updates)} Systems")


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

        # After the 3.30.0 migration, we can start parsing each version incrementally
        if not previous_config or Version(previous_config.get("version")) < Version(
            "3.30.0"
        ):
            ensure_v2_to_v3_model_migration()
            ensure_v3_24_model_migration()
            ensure_v3_27_model_migration()
            ensure_v3_29_model_migration()
            ensure_v3_30_model_migration()
