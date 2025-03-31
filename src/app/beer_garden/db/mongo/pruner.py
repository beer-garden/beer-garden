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
            projected_delete = (
                task["collection"].objects(query).only("id").no_cache().count()
            )

            if projected_delete > 0:
                if task["batch_size"] > 0:
                    while (
                        task["batch_size"]
                        < task["collection"]
                        .objects(query)
                        .only("id")
                        .no_cache()
                        .count()
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

                        task["collection"].objects(query).exclude(
                            *exclude_fields
                        ).limit(task["batch_size"]).no_cache().delete()

                task["collection"].objects(query).exclude(
                    *exclude_fields
                ).no_cache().delete()

                logger.debug(
                    "Deleted %s %s from %ss"
                    % (projected_delete, ttl_name, task["collection"].__name__)
                )


def prune_by_name(ttl_name):
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
    orphan_ttl = config.get(config.get("db.prune.interval"))

    if orphan_ttl > 0:
        prune_orphan_command_type(orphan_ttl, "INFO")
        prune_orphan_command_type(orphan_ttl, "ACTION")
        prune_orphan_command_type(orphan_ttl, "ADMIN")
        prune_orphan_command_type(orphan_ttl, "TEMP")
        prune_orphan_files(orphan_ttl)


def prune_orphan_files(ttl):
    timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)

    orphaned_files = File.objects.only("request", "job", "id", "owner_type").filter(
        updated_at__lte=timeout,
    )

    for file in orphaned_files:
        try:
            if file.owner_type == "JOB" and file.job is not None:
                Job.objects.get(id=file.job.id)
            elif file.owner_type == "REQUEST" and file.request is not None:
                Request.objects.get(id=file.request.id)
        except DoesNotExist:
            logger.error(f"File missing owner, killing orphan file {file.id}")
            file.delete()


def prune_orphan_command_type(ttl, command_type):
    timeout = datetime.now(timezone.utc) - timedelta(minutes=ttl)

    orphaned_requests = Request.objects.only("parent", "id").filter(
        command_type=command_type,
        status__in=["CANCELED", "SUCCESS", "ERROR", "INVALID"],
        created_at__lte=timeout,
        has_parent=True,
    )

    for request in orphaned_requests:
        try:
            Request.objects.get(id=request.parent.id)
        except DoesNotExist:
            logger.error(f"Parent is missing, killing orphan request {request.id}")
            request.delete()


def prune_outstanding():
    """
    Helper function for run to mark requests still outstanding after a certain
    amount of time as canceled.
    """
    prune_config = config.get("db.prune")
    cancel_threshold = prune_config.get("in_progress_request_expiration", -1)
    if cancel_threshold > 0:
        timeout = datetime.utcnow() - timedelta(minutes=cancel_threshold)
        outstanding_requests = Request.objects.filter(
            status__in=["IN_PROGRESS", "CREATED"], created_at__lte=timeout
        )
        # TODO: Sorting in reverse order, so newest first

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
            except ModelValidationError as ex:
                logger.error(ex)
                logger.error("Will attempt to check for parents")

                if request.has_parent:
                    try:
                        Request.objects.get(id=request.parent.id)
                    except DoesNotExist:
                        logger.error(
                            f"Parent is missing, killing orphan request {request.id}"
                        )
                        request.delete()


def prune_grid_fs():
    """
    Helper function to remove files from GridFS that are no longer
    referenced by the database.
    """

    prune_config_ttl = config.get("db.prune.ttl")
    file_threshold = prune_config_ttl.get("file", -1)
    timeout = datetime.now(timezone.utc) - timedelta(minutes=file_threshold)

    db = get_db()
    files = db["fs.files"]
    outstanding_files = files.find({"uploadDate": {"$lte": timeout}})

    for outstanding_file in outstanding_files:
        if (
            Request.objects.filter(
                Q(output_gridfs=outstanding_file["_id"])
                | Q(parameters_gridfs=outstanding_file["_id"])
            ).count()
            == 0
            and RawFile.objects.filter(file=outstanding_file["_id"]).count() == 0
        ):

            db["fs.chunks"].delete_many({"files_id": outstanding_file["_id"]})
            files.delete_one({"_id": outstanding_file["_id"]})
            logger.error(f"Deleted orphaned file {outstanding_file['_id']}")
