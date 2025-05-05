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
from beer_garden.db.mongo.models import File, Job, RawFile, Request
from beer_garden.db.mongo.parser import MongoParser
from beer_garden.events import publish
from beer_garden.metrics import CollectMetrics

logger = logging.getLogger(__name__)

display_name = "Mongo Pruner"


def prune_requests(ttl_length, command_type):

    if ttl_length <= 0:
        return

    batch_size = config.get("db.prune.batch_size")
    delete_older_than = datetime.utcnow() - timedelta(minutes=ttl_length)

    query = (
        Q(**{"created_at__lt": delete_older_than})
        & (Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR"))
        & Q(has_parent=False)
    )

    if command_type == "ACTION":
        # If the command type is ACTION, we need to check for requests that
        # have no command type or have a command type of None
        query = query & (
            Q(command_type="ACTION")
            | Q(command_type=None)
            | Q(command_type__exists=False)
        )
    else:
        query = query & Q(command_type=command_type)

    if batch_size > 0:
        request_cursor = (
            Request.objects(query)
            .only("id", "output_gridfs", "parameters_gridfs", "parameters")
            .batch_size(batch_size)
        )
    else:
        request_cursor = Request.objects(query).only(
            "id", "output_gridfs", "parameters_gridfs", "parameters"
        )

    prune_request_cursor(request_cursor, batch_size, command_type)


def prune_request_cursor(request_cursor, batch_size, label, orphan_check=False):

    request_ids = []
    request_raw_files = []
    request_grids_fs_files = []

    try:
        prune_request_cursor_loop(
            request_cursor,
            batch_size,
            request_ids,
            request_raw_files,
            request_grids_fs_files,
            orphan_check,
        )

        if batch_size > 0:
            for raw_file in RawFile.objects(Q(id__in=request_raw_files)).batch_size(
                batch_size
            ):
                request_grids_fs_files.append(raw_file.file._id)
        else:
            for raw_file in RawFile.objects(Q(id__in=request_raw_files)):
                request_grids_fs_files.append(raw_file.file._id)
    finally:
        if len(request_ids) > 0:
            db = get_db()

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
                    db["request"].delete_many({"_id": {"$in": batch}})

            else:
                db["raw_files"].delete_many({"_id": {"$in": request_raw_files}})
                db["fs.chunks"].delete_many(
                    {"files_id": {"$in": request_grids_fs_files}}
                )
                db["fs.files"].delete_many({"_id": {"$in": request_grids_fs_files}})
                db["request"].delete_many({"_id": {"$in": request_ids}})

            db["file"].update_many(
                {"requests": {"$in": request_ids}},
                {"$set": {"request": None}},
            )

            logger.error(f"{len(request_ids)} {label} Requests deleted")

            if len(request_grids_fs_files) > 0:
                logger.error(
                    f"{len(request_grids_fs_files)} GridFS files deleted "
                    f"for {label} Requests"
                )

            if len(request_raw_files) > 0:
                logger.error(
                    f"{len(request_raw_files)} Raw files deleted "
                    f"for {label} Requests"
                )

        else:
            logger.debug(f"No {label} Requests deleted")


def prune_request_cursor_loop(
    request_cursor,
    batch_size,
    request_ids,
    request_raw_files,
    request_grids_fs_files,
    orphan_check=False,
):
    """
    Helper function to prune a cursor of requests
    """

    batch_ids = []
    for request in request_cursor:
        try:
            if orphan_check:
                if not request.has_parent:
                    continue

                try:
                    if Request.objects.with_id(request.parent.id):
                        continue
                except DoesNotExist:
                    pass

            request_ids.append(request.id)
            batch_ids.append(request.id)
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

        except DoesNotExist:
            logger.error(
                f"DoesNotExist: Attempted to delete request {request.id} "
                "but does not exist in database"
            )

    if len(batch_ids) > 0:
        if batch_size is not None and batch_size > 0:
            prune_request_cursor_loop(
                Request.objects.filter(parent__in=batch_ids)
                .only("id", "output_gridfs", "parameters_gridfs", "parameters")
                .batch_size(batch_size),
                batch_size,
                request_ids,
                request_raw_files,
                request_grids_fs_files,
            )
        else:
            prune_request_cursor_loop(
                Request.objects.filter(parent__in=batch_ids).only(
                    "id", "output_gridfs", "parameters_gridfs", "parameters"
                ),
                batch_size,
                request_ids,
                request_raw_files,
                request_grids_fs_files,
            )


def prune_info_requests():

    ttl_length = config.get("db.prune.ttl.info")

    prune_requests(
        ttl_length,
        "INFO",
    )


def prune_action_requests():
    ttl_length = config.get("db.prune.ttl.action")

    prune_requests(
        ttl_length,
        "ACTION",
    )


def prune_admin_requests():

    ttl_length = config.get("db.prune.interval", default=15)

    prune_requests(
        ttl_length,
        "ADMIN",
    )


def prune_temp_requests():
    ttl_length = config.get("db.prune.interval", default=15)

    prune_requests(
        ttl_length,
        "TEMP",
    )


def prune_files():
    ttl_length = config.get("db.prune.ttl.file")

    if ttl_length > 0:

        file_ids = []
        raw_file_ids = []
        gridfs_ids = []

        delete_older_than = datetime.utcnow() - timedelta(minutes=ttl_length)

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
            "status__in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"],
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
            "created_at__lte": timeout,
            "has_parent": True,
        }

        batch_size = config.get("db.prune.batch_size")

        if batch_size > 0:

            orphaned_requests = (
                Request.objects.only(
                    "has_parent",
                    "parent",
                    "id",
                    "output_gridfs",
                    "parameters_gridfs",
                    "parameters",
                )
                .filter(**filter)
                .batch_size(batch_size)
            )

        else:
            orphaned_requests = Request.objects.only(
                "has_parent",
                "parent",
                "id",
                "output_gridfs",
                "parameters_gridfs",
                "parameters",
            ).filter(**filter)

        prune_request_cursor(
            orphaned_requests, batch_size, f"Orphaned {command_type}", orphan_check=True
        )


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
