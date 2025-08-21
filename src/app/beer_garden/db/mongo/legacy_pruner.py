# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone

from mongoengine import Q
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist

import beer_garden.config as config
from beer_garden.db.mongo.models import File, Job, RawFile, Request
from beer_garden.metrics import CollectMetrics

logger = logging.getLogger(__name__)

display_name = "Legacy Mongo Pruner"


def prune_by_name(ttl_name):
    with CollectMetrics("PRUNER", f"Pruner::{ttl_name}"):
        prune_requests(ttl_name)


def prune_info_requests():
    prune_by_name("info")


def prune_action_requests():
    prune_by_name("action")


def prune_admin_requests():
    prune_by_name("admin")


def prune_temp_requests():
    prune_by_name("temp")


def prune_requests(ttl_name):

    batch_size = config.get("db.prune.batch_size")
    current_time = datetime.now(timezone.utc)

    if ttl_name in ["admin", "temp"]:
        ttl_length = config.get("db.prune.interval", default=15)
    else:
        ttl_length = config.get(f"db.prune.ttl.{ttl_name}")

    query = Q(updated_at__lt=current_time - timedelta(minutes=ttl_length)) & (
        Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
    )

    if ttl_name == "admin":
        query = query & Q(has_parent=False) & Q(command_type="ADMIN")
    elif ttl_name == "temp":
        query = query & Q(command_type="TEMP")
    elif ttl_name == "action":
        query = (
            query
            & Q(has_parent=False)
            & (
                Q(command_type="ACTION")
                | Q(command_type=None)
                | Q(command_type__exists=False)
            )
        )
    elif ttl_name == "info":
        query = query & Q(has_parent=False) & Q(command_type="INFO")

    request_cursor = Request.objects(query).only(
        "id", "output_gridfs", "parameters_gridfs", "parameters"
    )

    request_ids = []
    request_raw_files = []
    request_grids_fs_files = []

    prune_request_cursor(
        request_cursor,
        batch_size,
        "Expired",
        request_ids,
        request_raw_files,
        request_grids_fs_files,
    )

    if len(request_ids) > 0:
        delete_requests(
            batch_size,
            request_ids,
            request_raw_files,
            request_grids_fs_files,
            "Expired",
        )


def prune_request_cursor(
    request_cursor,
    batch_size,
    label,
    request_ids,
    request_raw_files,
    request_grids_fs_files,
):
    """
    Helper function to prune a cursor of requests
    request_ids, request_raw_files, request_grids_fs_files modify the list in place
    so parent function can access for final delete
    """
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

            # Get children
            if request:
                child_cursor = Request.objects(parent=request).only(
                    "id", "output_gridfs", "parameters_gridfs", "parameters"
                )
                prune_request_cursor(
                    child_cursor,
                    batch_size,
                    label,
                    request_ids,
                    request_raw_files,
                    request_grids_fs_files,
                )

        except DoesNotExist:
            logger.error(
                f"DoesNotExist: Attempted to delete request {request.id} "
                "but does not exist in database"
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


def prune_files():
    ttl_length = config.get("db.prune.ttl.file")

    if ttl_length > -1:

        file_ids = []
        raw_file_ids = []
        gridfs_ids = []

        delete_older_than = datetime.now(timezone.utc) - timedelta(minutes=ttl_length)
        batch_size = config.get("db.prune.batch_size")

        try:
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
                if batch_size > 0 and len(file_ids) > batch_size:
                    delete_files(
                        batch_size, file_ids, raw_file_ids, gridfs_ids, "Expired"
                    )

            for raw_file in RawFile.objects(Q(created_at__lt=delete_older_than)):
                raw_file_ids.append(raw_file.id)
                gridfs_ids.append(raw_file.file.grid_id)
                if batch_size > 0 and len(raw_file_ids) > batch_size:
                    delete_files(
                        batch_size, file_ids, raw_file_ids, gridfs_ids, "Expired"
                    )

        finally:
            if len(file_ids) > 0 or len(raw_file_ids) > 0:
                delete_files(batch_size, file_ids, raw_file_ids, gridfs_ids, "Expired")


def delete_files(batch_size, file_ids, raw_file_ids, gridfs_ids, label):
    db = get_db()

    if batch_size > 0:
        for batch in [
            file_ids[i : i + batch_size] for i in range(0, len(file_ids), batch_size)
        ]:
            db["file_chunks"].delete_many({"files_id": {"$in": batch}})
            db["file"].delete_many({"_id": {"$in": batch}})

        for batch in [
            raw_file_ids[i : i + batch_size]
            for i in range(0, len(raw_file_ids), batch_size)
        ]:
            db["raw_files"].delete_many({"_id": {"$in": batch}})

        for batch in [
            gridfs_ids[i : i + batch_size]
            for i in range(0, len(raw_file_ids), batch_size)
        ]:
            db["fs.chunks"].delete_many({"files_id": {"$in": batch}})
            db["fs.files"].delete_many({"_id": {"$in": batch}})
    else:
        db["file_chunks"].delete_many({"files_id": {"$in": file_ids}})
        db["file"].delete_many({"_id": {"$in": file_ids}})

        db["raw_files"].delete_many({"_id": {"$in": raw_file_ids}})
        db["fs.chunks"].delete_many({"files_id": {"$in": gridfs_ids}})
        db["fs.files"].delete_many({"_id": {"$in": gridfs_ids}})

    logger.error(f"{len(file_ids)} {label} Files deleted")

    if len(gridfs_ids) > 0:
        logger.debug(f"{len(gridfs_ids)} GridFS files deleted " f"for {label} Files")

    if len(raw_file_ids) > 0:
        logger.debug(f"{len(raw_file_ids)} Raw files deleted for {label} Files")


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
                    Job.objects.get(id=file.job.id)
                elif file.owner_type == "REQUEST" and file.request is not None:
                    Request.objects.get(id=file.request.id)
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
            "status__in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"],
            "updated_at__lte": timeout,
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


def prune_orphan_command_type_info():
    prune_orphan_command_type("INFO")


def prune_orphan_command_type_action():
    prune_orphan_command_type("ACTION")


def prune_orphan_command_type_admin():
    prune_orphan_command_type("ADMIN")


def prune_orphan_command_type(command_type):
    with CollectMetrics("PRUNER", f"Pruner::orphan_{command_type}"):
        ttl = config.get("db.prune.interval", default=15)

        if command_type == "ACTION":
            cmd_ttl_length = config.get("db.prune.ttl.action")
            if cmd_ttl_length > 0:
                ttl = ttl + cmd_ttl_length
        elif command_type == "INFO":
            cmd_ttl_length = config.get("db.prune.ttl.info")
            if cmd_ttl_length > 0:
                ttl = ttl + cmd_ttl_length

        timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)
        filter = {
            "command_type": command_type,
            "status__in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"],
            "updated_at__lte": timeout,
            "has_parent": True,
        }

        batch_size = config.get("db.prune.batch_size")

        if batch_size > 0:

            orphaned_requests = (
                Request.objects.only("parent", "id")
                .filter(**filter)
                .batch_size(batch_size)
            )
            prune_orphan_requests(
                orphaned_requests, command_type, batch_size=batch_size
            )

        else:
            orphaned_requests = Request.objects.only("parent", "id").filter(**filter)
            prune_orphan_requests(orphaned_requests, command_type)


def prune_orphan_requests(orphaned_requests, command_type, batch_size=None):
    counter = 0
    try:
        for request in orphaned_requests:
            try:
                Request.objects.get(id=request.parent.id)
            except DoesNotExist:
                request.delete()
                counter = counter + 1

    finally:

        if counter > 0:
            logger.error(
                (
                    f"{counter} orphaned {command_type} Requests deleted "
                    f"{', batch size: ' + str(batch_size) if batch_size else ''}"
                )
            )

        else:
            logger.debug(
                (
                    f"No orphaned {command_type} Requests "
                    f"{', batch size: ' + str(batch_size) if batch_size else ''}"
                )
            )
