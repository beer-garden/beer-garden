# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events
from brewtils.schema_parser import SchemaParser
from mongoengine import FileField, ObjectIdField, Q
from mongoengine.connection import get_db
from mongoengine.errors import DoesNotExist

import beer_garden.config as config
from beer_garden.db.mongo.models import File, Job, RawFile, Request
from beer_garden.db.mongo.parser import MongoParser
from beer_garden.events import publish
from beer_garden.metrics import CollectMetrics

logger = logging.getLogger(__name__)

display_name = "Mongo Pruner"


def run_pruner(tasks, ttl_name):
    current_time = datetime.utcnow()

    if tasks:
        for task in tasks:
            exclude_fields = []

            for field in task["collection"]._fields:
                if not isinstance(
                    task["collection"]._fields[field], FileField
                ) and not isinstance(task["collection"]._fields[field], ObjectIdField):
                    exclude_fields.append(field)

            delete_older_than = current_time - task["delete_after"]

            query = Q(**{task["field"] + "__lt": delete_older_than})
            if task.get("additional_query", None):
                query = query & task["additional_query"]

            logger.debug(
                "Removing %s %ss older than %s"
                % (ttl_name, task["collection"].__name__, str(delete_older_than))
            )

            removed_count = 0

            if task["batch_size"] > 0:
                while (
                    task["batch_size"]
                    < task["collection"].objects(query).only("id").no_cache().count()
                ):
                    logger.debug(
                        "Removing %s from %ss older than %s, batched by %s"
                        % (
                            ttl_name,
                            task["collection"].__name__,
                            str(delete_older_than),
                            str(task["batch_size"]),
                        )
                    )
                    for record in (
                        task["collection"]
                        .objects(query)
                        .only("id")
                        .limit(task["batch_size"])
                    ):
                        record.delete()
                        removed_count = removed_count + 1

            for record in task["collection"].objects(query).only("id"):
                record.delete()
                removed_count = removed_count + 1

            if removed_count > 0:
                logger.debug(
                    "Deleted %s %s from %ss"
                    % (removed_count, ttl_name, task["collection"].__name__)
                )


def prune_by_name(ttl_name):
    with CollectMetrics("PRUNER", f"Pruner::{ttl_name}"):
        if ttl_name in ["admin", "temp"]:
            ttl_length = config.get("db.prune.interval")
        else:
            ttl_length = config.get(f"db.prune.ttl.{ttl_name}")

        tasks = determine_tasks(ttl_name, ttl_length)
        run_pruner(tasks, ttl_name)


def prune_info_requests():
    prune_by_name("info")


def prune_action_requests():
    prune_by_name("action")


def prune_admin_requests():
    prune_by_name("admin")


def prune_temp_requests():
    prune_by_name("temp")


def prune_files():
    prune_by_name("file")


def determine_tasks(ttl_name, ttl_length) -> Tuple[List[dict], int]:
    """Determine tasks and run interval from TTL values

    Args:
        ttl_name: Name of ttl type
        ttl_length: Length of time to wait before running pruner

    Returns:
        A tuple that contains:
            - A list of task configurations
            - The suggested interval between runs

    """
    prune_tasks = []
    batch_size = config.get("db.prune.batch_size")
    if ttl_length <= 0:
        return []
    if ttl_name == "info":
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=ttl_length),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & Q(command_type="INFO"),
            }
        )

    if ttl_name == "action":
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=ttl_length),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & (
                    Q(command_type="ACTION")
                    | Q(command_type=None)
                    | Q(command_type__exists=False)
                ),
            }
        )

    if ttl_name == "admin":
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=ttl_length),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & Q(command_type="ADMIN"),
            }
        )

    if ttl_name == "temp":
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=ttl_length),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & Q(command_type="TEMP"),
            }
        )

    if ttl_name == "file":
        prune_tasks.append(
            {
                "collection": File,
                "batch_size": batch_size,
                "field": "updated_at",
                "delete_after": timedelta(minutes=ttl_length),
                "additional_query": Q(owner_type=None)  # No one has claimed me
                | (
                    (Q(owner_type__iexact="JOB") & Q(job=None))
                    | (  # A Job claimed me, but it's gone now
                        Q(owner_type__iexact="REQUEST") & Q(request=None)
                    )  # A request claimed me, but it's gone
                ),
            }
        )
        prune_tasks.append(
            {
                "collection": RawFile,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=ttl_length),
            }
        )

    return prune_tasks


def prune_orphans():
    with CollectMetrics("PRUNER", "Pruner::orphans"):
        orphan_ttl = config.get("db.prune.interval")

        if orphan_ttl > 0:
            prune_orphan_command_type(orphan_ttl, "INFO")
            prune_orphan_command_type(orphan_ttl, "ACTION")
            prune_orphan_command_type(orphan_ttl, "ADMIN")
            prune_missed_temp_command(orphan_ttl)
            prune_orphan_files(orphan_ttl)


def prune_orphan_files(ttl):
    with CollectMetrics("PRUNER", "Pruner::orphan_files"):
        timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)

        batch_size = config.get("db.prune.batch_size")
        if batch_size > 0:

            total_files = (
                File.objects.only("request", "job", "id", "owner_type")
                .filter(
                    updated_at__lte=timeout,
                )
                .count()
                + 1
            )

            batches = round(total_files / batch_size) + 1

            for i in range(batches, 0, -1):
                orphaned_files = (
                    File.objects.only("request", "job", "id", "owner_type")
                    .filter(
                        updated_at__lte=timeout,
                    )
                    .limit(batch_size)
                    .skip(batch_size * (i - 1))
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
    for file in orphaned_files:
        try:
            if file.owner_type == "JOB" and file.job is not None:
                Job.objects.get(id=file.job.id)
            elif file.owner_type == "REQUEST" and file.request is not None:
                Request.objects.get(id=file.request.id)
        except DoesNotExist:
            file.delete()
            counter = counter + 1

    if counter > 0:
        logger.error(f"{counter} Files missing owner, deleted orphans")

    else:
        logger.debug("No missed owners for Files")


def prune_missed_temp_command(ttl):
    with CollectMetrics("PRUNER", "Pruner::orphan_missed_temp"):
        timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)
        filter = {
            "command_type": "TEMP",
            "status__in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"],
            "created_at__lte": timeout,
            "has_parent": True,
        }

        batch_size = config.get("db.prune.batch_size")

        if batch_size > 0:
            total_requests = (
                Request.objects.only("parent", "id").filter(**filter).count() + 1
            )

            batches = round(total_requests / batch_size) + 1

            for i in range(batches, 0, -1):
                temp_requests = (
                    Request.objects.only("parent", "id")
                    .filter(**filter)
                    .limit(batch_size)
                    .skip(batch_size * (i - 1))
                )
                prune_missed_temp_requests(temp_requests)

        else:
            temp_requests = Request.objects.only("parent", "id").filter(**filter)
            prune_missed_temp_requests(temp_requests)


def prune_missed_temp_requests(temp_requests):
    counter = 0
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

    if counter > 0:
        logger.error(
            f"{counter} TEMP Requests deleted due to Parent Request is completed or missing"
        )

    else:
        logger.debug("No missed TEMP Requests")


def prune_orphan_command_type(ttl, command_type):
    with CollectMetrics("PRUNER", f"Pruner::orphan_{command_type}"):
        timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)
        filter = {
            "command_type": command_type,
            "status__in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"],
            "created_at__lte": timeout,
            "has_parent": True,
        }

        batch_size = config.get("db.prune.batch_size")

        if batch_size > 0:
            total_requests = (
                Request.objects.only("parent", "id").filter(**filter).count() + 1
            )

            batches = round(total_requests / batch_size) + 1

            for i in range(batches, 0, -1):
                orphaned_requests = (
                    Request.objects.only("parent", "id")
                    .filter(**filter)
                    .limit(batch_size)
                    .skip(batch_size * (i - 1))
                )
                prune_orphan_requests(orphaned_requests, command_type)

        else:
            orphaned_requests = Request.objects.only("parent", "id").filter(**filter)
            prune_orphan_requests(orphaned_requests, command_type)


def prune_orphan_requests(orphaned_requests, command_type):
    counter = 0
    for request in orphaned_requests:
        try:
            Request.objects.get(id=request.parent.id)
        except DoesNotExist:
            request.delete()
            counter = counter + 1

    if counter > 0:
        logger.error(f"{counter} orphaned {command_type} Requests deleted")

    else:
        logger.debug(f"No orphaned {command_type} Requests")


def prune_outstanding():
    """
    Helper function for run to mark requests still outstanding after a certain
    amount of time as canceled.
    """
    with CollectMetrics("PRUNER", "Pruner::outstanding"):
        prune_config = config.get("db.prune")
        cancel_threshold = prune_config.get("in_progress_request_expiration", -1)
        if cancel_threshold > 0:
            timeout = datetime.utcnow() - timedelta(minutes=cancel_threshold)
            batch_size = config.get("db.prune.batch_size")

            if batch_size > 0:
                while (
                    batch_size
                    < Request.objects.filter(
                        status__in=["IN_PROGRESS", "CREATED"], created_at__lte=timeout
                    )
                    .no_cache()
                    .count()
                ):
                    outstanding_requests = Request.objects.filter(
                        status__in=["IN_PROGRESS", "CREATED"], created_at__lte=timeout
                    ).limit(batch_size)
                    prune_outstanding_requests(outstanding_requests)

            outstanding_requests = Request.objects.filter(
                status__in=["IN_PROGRESS", "CREATED"], created_at__lte=timeout
            )
            # TODO: Sorting in reverse order, so newest first
            prune_outstanding_requests(outstanding_requests)


def prune_outstanding_requests(outstanding_requests):
    counter = 0
    for request in outstanding_requests:
        try:
            request.status = "CANCELED"
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
        prune_config_ttl = config.get("db.prune.ttl")
        file_threshold = prune_config_ttl.get("file", -1)
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
                    prune_grid_fs_files(db, files, outstanding_files)

        else:
            outstanding_files = files.find(filter, {"_id": 1})
            prune_grid_fs_files(db, files, outstanding_files)


def prune_grid_fs_files(db, files, outstanding_files):

    outstanding_ids = []
    for outstanding_file in outstanding_files:
        if db["request"].find_one(
            {
                "$or": [
                    {"output_gridfs": outstanding_file["_id"]},
                    {"parameters_gridfs": outstanding_file["_id"]},
                ]
            },
            {"_id": 1},
        ) is None and (
            "raw_file" not in db
            or db["raw_file"].find_one(
                {"file": outstanding_file["_id"]},
                {"_id": 1},
            )
            is None
        ):
            outstanding_ids.append(outstanding_file["_id"])

            # Request.objects(
            #     Q(output_gridfs=outstanding_file["_id"])
            #     | Q(parameters_gridfs=outstanding_file["_id"])
            # ).count()
            # == 0
            # and RawFile.objects(Q(file=outstanding_file["_id"])).count() == 0
    counter = len(outstanding_ids)

    if counter > 0:
        db["fs.chunks"].delete_many({"files_id": {"$in": outstanding_ids}})
        files.delete_many({"_id": {"$in": outstanding_ids}})
        logger.error(f"Deleted {counter} orphaned files from GridFS")

    else:
        logger.error("No orphaned files found in GridFS")
