# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events
from brewtils.models import Request as BrewtilsRequest
from mongoengine import Q
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist
from pymongo import UpdateOne

import beer_garden.config as config
from beer_garden.db.mongo.api import to_brewtils
from beer_garden.db.mongo.models import File, FileChunk, RawFile, Request
from beer_garden.events import publish
from beer_garden.metrics import CollectMetrics

logger = logging.getLogger(__name__)

display_name = "Mongo Pruner"


def completed_status_query():
    query = None
    for status in BrewtilsRequest.COMPLETED_STATUSES:
        if query:
            query = query | Q(status=status)
        else:
            query = Q(status=status)
    return query


def determine_expiration_at(request, action_ttl, info_ttl):
    if request.expiration_at:
        return request.expiration_at

    if request.has_parent:
        try:
            parent = Request.objects.get(id=request.parent.id)

            if parent.expiration_at:
                # Parent has an expiration, so we will just use that
                return request.expiration_at
            if parent.status not in BrewtilsRequest.COMPLETED_STATUSES:
                # Parent is still running
                return None
            return determine_expiration_at(parent, action_ttl, info_ttl)
        except DoesNotExist:
            pass

    if action_ttl > -1 and request.root_command_type == "ACTION":
        return request.created_at + timedelta(minutes=action_ttl)

    if info_ttl > -1 and request.root_command_type == "INFO":
        return request.created_at + timedelta(minutes=info_ttl)

    # Must be Admin or Temp
    return request.created_at


def find_missing_expiration_requests():
    """
    Find Requests that do not have expiration_at dates set but should have. Then set
    them to the most accurate value we can calculate base on what is in the database
    """

    batch_size = config.get("db.prune.batch_size")
    action_ttl = config.get("db.prune.ttl.action", default=-1)
    info_ttl = config.get("db.prune.ttl.info", default=-1)

    current_time = datetime.now(timezone.utc)

    missing_expiration_filter = None
    if action_ttl > -1:
        missing_expiration_filter = Q(
            created_at__lt=current_time - timedelta(minutes=action_ttl)
        ) & Q(root_command_type="ACTION")

    if info_ttl > -1:
        if not missing_expiration_filter:
            missing_expiration_filter = Q(
                created_at__lt=current_time - timedelta(minutes=info_ttl)
            ) & Q(root_command_type="INFO")
        else:
            missing_expiration_filter = (missing_expiration_filter) | (
                Q(created_at__lt=current_time - timedelta(minutes=info_ttl))
                & Q(root_command_type="INFO")
            )

    if not missing_expiration_filter:
        return

    query = (
        Q(expiration_at=None) & (completed_status_query()) & (missing_expiration_filter)
    )

    updates = []
    for request in Request.objects(query).only(
        "id", "parent", "has_parent", "created_at", "expiration_at", "root_command_type"
    ):
        expiration_at = determine_expiration_at(request, action_ttl, info_ttl)

        if expiration_at:
            updates.append(
                UpdateOne(
                    {"_id": request.id},
                    {"$set": {"expiration_at": expiration_at}},
                )
            )

            # Bulk update early if the list gets over batch size
            if batch_size > 0 and len(updates) > batch_size:
                Request._get_collection().bulk_write(updates, ordered=False)
                logger.warning(f"Recomputed {len(updates)} missing Request TTLs")
                updates = []

    # Bulk update any updates needed to correct expiration dates
    if len(updates) > 0:
        Request._get_collection().bulk_write(updates, ordered=False)
        logger.warning(f"Recomputed {len(updates)} missing Request TTLs")


def prune_requests():

    batch_size = config.get("db.prune.batch_size")
    current_time = datetime.now(timezone.utc)

    query = completed_status_query() & (
        Q(expiration_at__lt=current_time)
        | ((Q(command_type="ADMIN") | Q(command_type="TEMP")))
    )

    request_cursor = Request.objects(query).only(
        "id", "output_gridfs", "parameters_gridfs", "parameters"
    )

    prune_request_cursor(request_cursor, batch_size, "Expired")


def prune_request_cursor(
    request_cursor,
    batch_size,
    label,
):
    """
    Helper function to prune a cursor of requests
    """

    request_ids = []
    request_raw_files = []
    request_grids_fs_files = []

    for request in request_cursor:
        try:

            request_ids.append(request.id)

            if request.output_gridfs:
                try:
                    request_grids_fs_files.append(request.output_gridfs._id)
                except AttributeError:
                    logger.error(
                        f"AttributeError: Attempted to delete request {request.id} "
                        "but does not have a output_gridfs file id"
                    )
            if request.parameters_gridfs:
                try:
                    request_grids_fs_files.append(request.parameters_gridfs._id)
                except AttributeError:
                    logger.error(
                        f"AttributeError: Attempted to delete request {request.id} "
                        "but does not have a parameters_gridfs file id"
                    )

            parameters = request.parameters or {}

            for param_value in parameters.values():
                if (
                    isinstance(param_value, dict)
                    and param_value.get("type") == "bytes"
                    and param_value.get("id") is not None
                ):
                    request_raw_files.append(param_value["id"])

            if batch_size > 0 and len(request_ids) > batch_size:
                # Delete the batch of requests to keep in memory usage down
                delete_requests(
                    batch_size,
                    request_ids,
                    request_raw_files,
                    request_grids_fs_files,
                    label,
                )
                request_ids = []
                request_raw_files = []
                request_grids_fs_files = []

        except DoesNotExist:
            logger.error(
                f"DoesNotExist: Attempted to delete request {request.id} "
                "but does not exist in database"
            )

    if len(request_ids) > 0:
        delete_requests(
            batch_size,
            request_ids,
            request_raw_files,
            request_grids_fs_files,
            label,
        )


def delete_requests(
    batch_size, request_ids, request_raw_files, request_grids_fs_files, label
):

    db = get_db()

    if batch_size > 0:
        for batch in [
            request_raw_files[i : i + batch_size]
            for i in range(0, len(request_raw_files), batch_size)
        ]:
            raw_file_grid_fs = []
            for raw_file in RawFile.objects(Q(id__in=request_raw_files)):
                raw_file_grid_fs.append(raw_file.file.grid_id)
            if len(raw_file_grid_fs) > 0:
                db["fs.chunks"].delete_many({"files_id": {"$in": raw_file_grid_fs}})
                db["fs.files"].delete_many({"_id": {"$in": raw_file_grid_fs}})
            db["raw_files"].delete_many({"_id": {"$in": batch}})

        for batch in [
            request_grids_fs_files[i : i + batch_size]
            for i in range(0, len(request_grids_fs_files), batch_size)
        ]:
            db["fs.chunks"].delete_many({"files_id": {"$in": batch}})
            db["fs.files"].delete_many({"_id": {"$in": batch}})

        for batch in [
            request_ids[i : i + batch_size]
            for i in range(0, len(request_ids), batch_size)
        ]:
            db["file"].update_many(
                {"requests": {"$in": batch}},
                {"$set": {"request": None}},
            )
            db["request"].delete_many({"_id": {"$in": batch}})

    else:
        if len(request_raw_files) > 0:
            for raw_file in RawFile.objects(Q(id__in=request_raw_files)):
                request_grids_fs_files.append(raw_file.file.grid_id)

        db["fs.chunks"].delete_many({"files_id": {"$in": request_grids_fs_files}})
        db["fs.files"].delete_many({"_id": {"$in": request_grids_fs_files}})

        db["raw_files"].delete_many({"_id": {"$in": request_raw_files}})
        db["file"].update_many(
            {"requests": {"$in": request_ids}},
            {"$set": {"request": None}},
        )
        db["request"].delete_many({"_id": {"$in": request_ids}})

    logger.error(f"{len(request_ids)} {label} Requests deleted")

    if len(request_grids_fs_files) > 0:
        logger.debug(
            f"{len(request_grids_fs_files)} GridFS files deleted "
            f"for {label} Requests"
        )

    if len(request_raw_files) > 0:
        logger.debug(f"{len(request_raw_files)} Raw files deleted for {label} Requests")


def prune_raw_files():

    raw_file_pipeline = [
        {
            "$lookup": {
                "from": "request",
                "localField": "request",
                "foreignField": "_id",
                "as": "lookup_result",
            }
        },
        {"$match": {"lookup_result": {"$size": 0}}},
        {"$project": {"_id": 1, "file": 1}},
    ]

    raw_file_ids = []
    gridfs_ids = []

    for doc in RawFile._get_collection().aggregate(raw_file_pipeline):
        raw_file_ids.append(doc["_id"])
        gridfs_ids.append(doc["file"])

    if len(raw_file_ids) > 0:
        batch_size = config.get("db.prune.batch_size")
        db = get_db()
        if batch_size > 0:
            for i in range(0, len(raw_file_ids), batch_size):

                db["raw_file"].delete_many(
                    {"_id": {"$in": raw_file_ids[i : i + batch_size]}}
                )
                db["fs.chunks"].delete_many(
                    {"files_id": {"$in": gridfs_ids[i : i + batch_size]}}
                )
                db["fs.files"].delete_many(
                    {"_id": {"$in": gridfs_ids[i : i + batch_size]}}
                )
        else:
            db["raw_file"].delete_many({"_id": {"$in": raw_file_ids}})
            db["fs.chunks"].delete_many({"files_id": {"$in": gridfs_ids}})
            db["fs.files"].delete_many({"_id": {"$in": gridfs_ids}})
        logger.error(f"{len(raw_file_ids)} Raw Files missing request, deleted orphans")
    else:
        logger.debug("No missed requests for Raw Files")


def prune_files():
    # Pruning Orphaned Files that think they are associated with a Request or Job
    # but the Request or Job no longer exists in the database
    with CollectMetrics("PRUNER", "Pruner::files"):

        request_pipeline = [
            {
                "$match": {
                    "owner_type": "REQUEST",
                    "request": {"$ne": None},
                }
            },
            {
                "$lookup": {
                    "from": "request",
                    "localField": "request",
                    "foreignField": "_id",
                    "as": "lookup_result",
                }
            },
            {"$match": {"lookup_result": {"$size": 0}}},
            {"$project": {"_id": 1}},
        ]

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

        ttl_length = config.get("db.prune.ttl.file")

        if ttl_length > -1:
            delete_older_than = datetime.now(timezone.utc) - timedelta(
                minutes=ttl_length
            )

            pipeline_unassigned = [
                {
                    "$match": {
                        "$or": [
                            {
                                "owner_type": "JOB",
                                "job": None,
                            },
                            {
                                "owner_type": "REQUEST",
                                "request": None,
                            },
                        ],
                        "updated_at__lt": delete_older_than,
                    }
                },
                {"$project": {"_id": 1}},
            ]
        else:
            pipeline_unassigned = None

        file_delete_ids = []
        file_delete_ids_str = []

        for pipeline in [request_pipeline, job_pipeline, pipeline_unassigned]:
            if pipeline:
                for doc in File._get_collection().aggregate(pipeline):
                    file_delete_ids.append(doc["_id"])
                    file_delete_ids_str.append(str(doc["_id"]))

        if len(file_delete_ids) > 0:
            batch_size = config.get("db.prune.batch_size")

            if batch_size > 0:
                for i in range(0, len(file_delete_ids), batch_size):
                    File._get_collection().delete_many(
                        {"_id": {"$in": file_delete_ids[i : i + batch_size]}}
                    )
                    FileChunk._get_collection().delete_many(
                        {"file_id": {"$in": file_delete_ids_str[i : i + batch_size]}}
                    )
            else:
                File._get_collection().delete_many({"_id": {"$in": file_delete_ids}})
                FileChunk._get_collection().delete_many(
                    {"file_id": {"$in": file_delete_ids_str}}
                )
            logger.error(f"{len(file_delete_ids)} Files missing owner, deleted orphans")
        else:
            logger.debug("No missed owners for Files")


def prune_outstanding():
    """
    Helper function for run to mark requests still outstanding after a certain
    amount of time as canceled.

    Update the newest requests first to give the oldest a chance to finish before
    being canceled.
    """
    with CollectMetrics("PRUNER", "Pruner::outstanding"):
        prune_config = config.get("db.prune")
        cancel_threshold = prune_config.get("in_progress_request_expiration")
        if cancel_threshold > 0:
            timeout = datetime.utcnow() - timedelta(minutes=cancel_threshold)
            batch_size = config.get("db.prune.batch_size")

            if batch_size > 0:

                outstanding_requests = (
                    Request.objects.filter(
                        status__in=["IN_PROGRESS", "CREATED"],
                        created_at__lte=timeout,
                    )
                    .order_by("-created_at")
                    .batch_size(batch_size)
                )
                prune_outstanding_requests(outstanding_requests)

            else:
                outstanding_requests = Request.objects.filter(
                    status__in=["IN_PROGRESS", "CREATED"], created_at__lte=timeout
                ).order_by("-created_at")

                prune_outstanding_requests(outstanding_requests)


def prune_outstanding_requests(outstanding_requests):
    counter = 0
    try:
        for request in outstanding_requests:
            try:
                request.status = "CANCELED"
                request.status_updated_at = datetime.now(timezone.utc)
                request.save()

                parsed = to_brewtils(request)

                publish(
                    Event(
                        name=Events.REQUEST_CANCELED.name,
                        payload_type="Request",
                        payload=parsed,
                    )
                )
                counter = counter + 1
            except ModelValidationError as ex:
                logger.error(
                    f"ModelValidationError: Failed to update outstanding Request {request.id}"
                )
                logger.debug(ex)
                logger.debug("Will attempt to check for parents")

                if request.has_parent:
                    try:
                        if not Request.objects.with_id(request.parent.id):
                            raise DoesNotExist
                    except DoesNotExist:
                        logger.debug(
                            f"Parent is missing, killing orphan request {request.id}"
                        )
                        request.delete()
            except DoesNotExist:
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


def prune_grid_fs():
    """
    Helper function to remove files from GridFS that are no longer
    referenced by the database.
    """

    with CollectMetrics("PRUNER", "Pruner::grid_fs"):
        prune_config_ttl = config.get("db.prune.ttl", default=15)
        file_threshold = prune_config_ttl.get("file")

        max_request_size = max(
            [prune_config_ttl.get("info"), prune_config_ttl.get("action")]
        )
        if max_request_size > -1:
            if file_threshold > -1:
                file_threshold = file_threshold + max_request_size
            else:
                file_threshold = max_request_size

        if file_threshold > 0:
            timeout = datetime.now(timezone.utc) - timedelta(minutes=file_threshold)

            db = get_db()
            files = db["fs.files"]

            filter = {"uploadDate": {"$lte": timeout}}

            batch_size = config.get("db.prune.batch_size")

            if batch_size > 0:
                total_files = files.count_documents(filter) + 1

                batches = round(total_files / batch_size) + 1

                for i in range(batches, 0, -1):
                    with CollectMetrics("PRUNER", "Pruner::grid_fs::batch"):
                        outstanding_files = (
                            files.find(filter, {"_id": 1})
                            .limit(batch_size)
                            .skip(batch_size * (i - 1))
                        )
                        prune_grid_fs_files(db, files, list(outstanding_files))

            else:
                outstanding_files = files.find(filter, {"_id": 1})
                prune_grid_fs_files(db, files, list(outstanding_files))


def prune_grid_fs_files(db, files, outstanding_files):

    # Bulk Check for orphaned files
    outstanding_ids = []
    for outstanding_file in outstanding_files:
        outstanding_ids.append(outstanding_file["_id"])

    requests_matching = (
        Request.objects(
            Q(output_gridfs__in=outstanding_ids)
            | Q(parameters_gridfs__in=outstanding_ids)
        )
        .only("id")
        .count()
    )

    raw_files_matching = RawFile.objects(Q(file__in=outstanding_ids)).only("id").count()

    total_matching = requests_matching + raw_files_matching

    try:
        if total_matching > 0:
            # If there are any files that are still referenced, we need to check
            # each file individually to see if it is orphaned
            outstanding_ids = []

            for outstanding_file in outstanding_files:
                if (
                    Request.objects(
                        Q(output_gridfs=outstanding_file["_id"])
                        | Q(parameters_gridfs=outstanding_file["_id"])
                    )
                    .only("id")
                    .count()
                    == 0
                    and RawFile.objects(Q(file=outstanding_file["_id"]))
                    .only("id")
                    .count()
                    == 0
                ):
                    outstanding_ids.append(outstanding_file["_id"])
    finally:

        counter = len(outstanding_ids)

        if counter > 0:
            db["fs.chunks"].delete_many({"files_id": {"$in": outstanding_ids}})
            files.delete_many({"_id": {"$in": outstanding_ids}})
            logger.error(f"Deleted {counter} orphaned files from GridFS")

        else:
            logger.debug("No orphaned files found in GridFS")
