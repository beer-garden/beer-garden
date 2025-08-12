# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events
from brewtils.schema_parser import SchemaParser
from mongoengine import Q
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist

import beer_garden.config as config
from beer_garden.db.mongo.models import File, FileChunk, RawFile, Request
from beer_garden.db.mongo.parser import MongoParser
from beer_garden.events import publish
from beer_garden.metrics import CollectMetrics

logger = logging.getLogger(__name__)

display_name = "Mongo Pruner"


def prune_raw_files():
    # TODO: This function is a temporary solution to prune Raw Files that
    # are not associated with any Request. It should be replaced with a
    # more robust solution that utilizes the TTL index for pruning.

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

        # TODO: We should update the Request pipeline to utilize the TTL index pruning
        # and not the lookup. Until then, we will keep the lookup to ensure
        # we are deleting files that are not in use.
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


def cancel_outstanding():
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
            timeout = datetime.now(timezone.utc) - timedelta(minutes=cancel_threshold)
            batch_size = config.get("db.prune.batch_size")

            if batch_size > 0:

                outstanding_requests = (
                    Request.objects.filter(
                        status__in=["IN_PROGRESS", "CREATED"],
                        updated_at__lte=timeout,
                    )
                    .order_by("-updated_at")
                    .batch_size(batch_size)
                )
                cancel_outstanding_requests(outstanding_requests)

            else:
                outstanding_requests = Request.objects.filter(
                    status__in=["IN_PROGRESS", "CREATED"], updated_at__lte=timeout
                ).order_by("-updated_at")

                cancel_outstanding_requests(outstanding_requests)


def cancel_outstanding_requests(outstanding_requests):
    counter = 0
    try:
        for request in outstanding_requests:
            try:
                request.status = "CANCELED"
                request.status_updated_at = datetime.now(timezone.utc)
                request.save()
                serialized = MongoParser.serialize(request, to_string=True)
                parsed = SchemaParser.parse_request(
                    serialized, from_string=True, many=False
                )

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

                if request.has_parent and request.parent is not None:
                    try:
                        Request.objects.get(id=request.parent.id)
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
        if max_request_size > 0:
            if file_threshold > 0:
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
