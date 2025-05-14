# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events
from brewtils.models import Request as BrewtilsRequest
from brewtils.schema_parser import SchemaParser
from mongoengine import Q
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist
from pymongo import UpdateOne

import beer_garden.config as config
from beer_garden.db.mongo.models import File, Job, RawFile, Request
from beer_garden.db.mongo.parser import MongoParser
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


def find_orphans_requests():
    """
    Find Requests that do not have expiration_at dates set but should have. Then set
    them to the most accurate value we can calculate base on what is in the database
    """

    batch_size = config.get("db.prune.batch_size")
    action_ttl = config.get("db.prune.ttl.action", default=-1)
    info_ttl = config.get("db.prune.ttl.info", default=-1)
    interval = config.get("db.prune.interval", default=0)

    current_time = datetime.now(timezone.utc)

    orphan_filter = None
    if action_ttl > 0:
        orphan_filter = Q(
            created_at__lt=current_time - timedelta(minutes=action_ttl + interval)
        ) & Q(root_command_type="ACTION")

    if info_ttl > 0:
        if not orphan_filter:
            orphan_filter = Q(
                created_at__lt=current_time - timedelta(minutes=info_ttl + interval)
            ) & Q(root_command_type="INFO")
        else:
            orphan_filter = (orphan_filter) | (
                Q(created_at__lt=current_time - timedelta(minutes=info_ttl + interval))
                & Q(root_command_type="INFO")
            )

    if not orphan_filter:
        return

    query = Q(expiration_at=None) & (completed_status_query()) & (orphan_filter)

    orphan_updates = []
    for orphaned_request in Request.objects(query).only(
        "id", "parent", "has_parent", "created_at", "expiration_at", "root_command_type"
    ):

        try:
            if not orphaned_request.has_parent:
                # Expiration never got set, raise exception so it get set in except
                raise DoesNotExist()
            parent = Request.objects.get(id=orphaned_request.parent.id)
            # Check if parent has an expiration date set
            if parent.expiration_at:
                orphan_updates.append(
                    UpdateOne(
                        {"_id": orphaned_request.id},
                        {"$set": {"expiration_at": parent.expiration_at}},
                    )
                )
            elif parent.status in BrewtilsRequest.COMPLETED_STATUSES:
                # Parent finished by doesn't have it set, so it got orphaned as well
                if parent.has_parent:
                    # It is also a child request so don't do anything. With
                    # the assumption is that it's parent is still running
                    continue
                else:
                    # Expiration never got set, so lets set it for both
                    if orphaned_request.root_command_type == "ACTION":
                        orphan_updates.append(
                            UpdateOne(
                                {"_id": parent.id},
                                {
                                    "$set": {
                                        "expiration_at": parent.created_at
                                        + timedelta(minutes=action_ttl)
                                    }
                                },
                            )
                        )
                        orphan_updates.append(
                            UpdateOne(
                                {"_id": orphaned_request.id},
                                {
                                    "$set": {
                                        "expiration_at": parent.created_at
                                        + timedelta(minutes=action_ttl)
                                    }
                                },
                            )
                        )
                    elif orphaned_request.root_command_type == "INFO":
                        orphan_updates.append(
                            UpdateOne(
                                {"_id": parent.id},
                                {
                                    "$set": {
                                        "expiration_at": parent.created_at
                                        + timedelta(minutes=info_ttl)
                                    }
                                },
                            )
                        )
                        orphan_updates.append(
                            UpdateOne(
                                {"_id": orphaned_request.id},
                                {
                                    "$set": {
                                        "expiration_at": parent.created_at
                                        + timedelta(minutes=info_ttl)
                                    }
                                },
                            )
                        )
                    else:
                        orphan_updates.append(
                            UpdateOne(
                                {"_id": parent.id},
                                {"$set": {"expiration_at": parent.created_at}},
                            )
                        )
                        orphan_updates.append(
                            UpdateOne(
                                {"_id": orphaned_request.id},
                                {"$set": {"expiration_at": parent.created_at}},
                            )
                        )
        except DoesNotExist:
            # This is an orphaned request
            if orphaned_request.root_command_type == "ACTION":
                orphan_updates.append(
                    UpdateOne(
                        {"_id": orphaned_request.id},
                        {
                            "$set": {
                                "expiration_at": orphaned_request.created_at
                                + timedelta(minutes=action_ttl)
                            }
                        },
                    )
                )
            elif orphaned_request.root_command_type == "INFO":
                orphan_updates.append(
                    UpdateOne(
                        {"_id": orphaned_request.id},
                        {
                            "$set": {
                                "expiration_at": orphaned_request.created_at
                                + timedelta(minutes=info_ttl)
                            }
                        },
                    )
                )
            else:
                # TEMP and ADMIN Requests can get pruned right away
                orphan_updates.append(
                    UpdateOne(
                        {"_id": orphaned_request.id},
                        {"$set": {"expiration_at": orphaned_request.created_at}},
                    )
                )

        # Bulk update early if the list gets over batch size
        if len(orphaned_request) > batch_size:
            Request._get_collection().bulk_write(orphan_updates, ordered=False)
            orphaned_request = []

    # Bulk update any updates needed to correct expiration dates
    if len(orphan_updates) > 0:
        Request._get_collection().bulk_write(orphan_updates, ordered=False)


def prune_requests():

    batch_size = config.get("db.prune.batch_size")
    current_time = datetime.now(timezone.utc)

    query = Q(expiration_at__lt=current_time) | (
        (completed_status_query()) & (Q(command_type="ADMIN") | Q(command_type="TEMP"))
    )

    request_cursor = Request.objects(query).only(
        "id", "output_gridfs", "parameters_gridfs", "parameters"
    )

    prune_request_cursor(request_cursor, batch_size, "Expired Requests")


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
    requests_deleted = False

    try:
        for request in request_cursor:
            try:

                request_ids.append(request.id)
                if request.output_gridfs:
                    request_grids_fs_files.append(request.output_gridfs._id)
                if request.parameters_gridfs:
                    request_grids_fs_files.append(request.parameters_gridfs._id)

                parameters = request.parameters or {}

                for param_value in parameters.values():
                    if (
                        isinstance(param_value, dict)
                        and param_value.get("type") == "bytes"
                        and param_value.get("id") is not None
                    ):
                        request_raw_files.append(param_value["id"])

                if len(request_ids) > batch_size:
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
                    requests_deleted = True

            except DoesNotExist:
                logger.error(
                    f"DoesNotExist: Attempted to delete request {request.id} "
                    "but does not exist in database"
                )
    finally:
        if len(request_ids) > 0:
            delete_requests(
                batch_size,
                request_ids,
                request_raw_files,
                request_grids_fs_files,
                label,
            )
        elif not requests_deleted:
            logger.debug(f"No {label} Requests deleted")


def delete_requests(
    batch_size, request_ids, request_raw_files, request_grids_fs_files, label
):
    if len(request_ids) > 0:
        db = get_db()

        if len(request_raw_files) > 0:
            for raw_file in RawFile.objects(Q(id__in=request_raw_files)):
                request_grids_fs_files.append(raw_file.file._id)

        if batch_size > 0:
            for batch in [
                request_raw_files[i : i + batch_size]
                for i in range(0, len(request_raw_files), batch_size)
            ]:
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
            db["raw_files"].delete_many({"_id": {"$in": request_raw_files}})
            db["fs.chunks"].delete_many({"files_id": {"$in": request_grids_fs_files}})
            db["fs.files"].delete_many({"_id": {"$in": request_grids_fs_files}})
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
            logger.debug(
                f"{len(request_raw_files)} Raw files deleted for {label} Requests"
            )


def prune_files():
    ttl_length = config.get("db.prune.ttl.file")

    if ttl_length > 0:

        file_ids = []
        raw_file_ids = []
        gridfs_ids = []

        delete_older_than = datetime.now(timezone.utc) - timedelta(minutes=ttl_length)

        try:
            batch_size = config.get("db.prune.batch_size")

            if batch_size > 0:
                for file in (
                    File.objects(
                        Q(updated_at__lt=delete_older_than)
                        & (
                            (
                                Q(owner_type=None)
                                | (
                                    (Q(owner_type__iexact="JOB") & Q(job=None))
                                    | (
                                        Q(owner_type__iexact="REQUEST")
                                        & Q(request=None)
                                    )
                                )
                            )
                        )
                    )
                    .only("id")
                    .batch_size(batch_size)
                ):
                    file_ids.append(file.id)

                for raw_file in RawFile.objects(
                    Q(created_at__lt=delete_older_than)
                ).batch_size(batch_size):
                    raw_file_ids.append(raw_file.id)
                    gridfs_ids.append(raw_file.file.grid_id)

            else:
                for file in File.objects(
                    Q(updated_at__lt=delete_older_than)
                    & (
                        (
                            Q(owner_type=None)
                            | (
                                (Q(owner_type__iexact="JOB") & Q(job=None))
                                | (Q(owner_type__iexact="REQUEST") & Q(request=None))
                            )
                        )
                    )
                ).only("id"):
                    file_ids.append(file.id)

                for raw_file in RawFile.objects(Q(created_at__lt=delete_older_than)):
                    raw_file_ids.append(raw_file.id)
                    gridfs_ids.append(raw_file.file.grid_id)

        finally:
            db = get_db()

            db["file_chunks"].delete_many({"files_id": {"$in": file_ids}})
            db["file"].delete_many({"_id": {"$in": file_ids}})

            db["raw_files"].delete_many({"_id": {"$in": raw_file_ids}})
            db["fs.chunks"].delete_many({"files_id": {"$in": gridfs_ids}})
            db["fs.files"].delete_many({"_id": {"$in": gridfs_ids}})


def prune_orphan_files():
    with CollectMetrics("PRUNER", "Pruner::orphan_files"):
        ttl = config.get("db.prune.interval", default=15)
        if ttl < 0:
            return
        timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)

        batch_size = config.get("db.prune.batch_size")
        if batch_size > 0:
            orphaned_files = (
                File.objects.only("request", "job", "id", "owner_type")
                .filter(
                    updated_at__lte=timeout,
                )
                .batch_size(batch_size)
            )
            prune_orphan_file_records(orphaned_files)
        else:

            orphaned_files = File.objects.only(
                "request", "job", "id", "owner_type"
            ).filter(
                updated_at__lte=timeout,
            )
            prune_orphan_file_records(orphaned_files)


def prune_orphan_file_records(orphaned_files):
    counter = 0

    try:
        for file in orphaned_files:
            try:
                if file.owner_type == "JOB" and file.job is not None:
                    if not Job.objects.with_id(file.job.id):
                        raise DoesNotExist
                elif file.owner_type == "REQUEST" and file.request is not None:
                    if not Request.objects.with_id(file.request.id):
                        raise DoesNotExist
            except DoesNotExist:
                file.delete()
                counter = counter + 1
    finally:

        if counter > 0:
            logger.error(f"{counter} Files missing owner, deleted orphans")

        else:
            logger.debug("No missed owners for Files")


def prune_missed_temp_command():
    """
    If the completion event is missed for a TEMP event, clean up the
    Request from the database
    """
    with CollectMetrics("PRUNER", "Pruner::orphan_missed_temp"):
        ttl = config.get("db.prune.interval", default=15)
        if ttl < 0:
            return
        timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)
        filter = {
            "command_type": "TEMP",
            "status__in": BrewtilsRequest.COMPLETED_STATUSES,
            "created_at__lte": timeout,
            "has_parent": True,
        }

        batch_size = config.get("db.prune.batch_size")

        if batch_size > 0:

            temp_requests = (
                Request.objects.only("parent", "id")
                .filter(**filter)
                .batch_size(batch_size)
            )
            prune_missed_temp_requests(temp_requests)

        else:
            temp_requests = Request.objects.only("parent", "id").filter(**filter)
            prune_missed_temp_requests(temp_requests)


def prune_missed_temp_requests(temp_requests):
    counter = 0

    try:
        for request in temp_requests:
            try:
                Request.objects.get(
                    id=request.parent.id,
                    status__in=[
                        "CREATED",
                        "RECEIVED",
                        "IN_PROGRESS",
                    ],
                )
            except DoesNotExist:
                request.delete()
                counter = counter + 1
    finally:

        if counter > 0:
            logger.error(
                f"{counter} TEMP Requests deleted due to Parent Request is completed or missing"
            )

        else:
            logger.debug("No missed TEMP Requests")


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

                for i in range(batches, 0, default=-1):
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
