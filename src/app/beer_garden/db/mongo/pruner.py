# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from typing import List, Tuple

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events
from brewtils.schema_parser import SchemaParser
from mongoengine import Q
from mongoengine.errors import DoesNotExist

import beer_garden.config as config
from beer_garden.db.mongo.models import File, RawFile, Request
from beer_garden.db.mongo.parser import MongoParser
from beer_garden.events import publish

logger = logging.getLogger(__name__)

display_name = "Mongo Pruner"


def run_pruner(tasks, ttl_name):
    current_time = datetime.utcnow()

    if tasks:
        for task in tasks:
            delete_older_than = current_time - task["delete_after"]

            query = Q(**{task["field"] + "__lt": delete_older_than})
            if task.get("additional_query", None):
                query = query & task["additional_query"]

            logger.debug(
                "Removing %s %ss older than %s"
                % (ttl_name, task["collection"].__name__, str(delete_older_than))
            )

            if task["batch_size"] > 0:
                while (
                    task["batch_size"]
                    < task["collection"].objects(query).no_cache().count()
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
                    task["collection"].objects(query).limit(
                        task["batch_size"]
                    ).no_cache().delete()

            num = task["collection"].objects(query).no_cache().delete()
            if num:
                logger.debug(
                    "Deleted %s %s from %ss"
                    % (num, ttl_name, task["collection"].__name__)
                )


def prune_by_name(ttl_name):
    ttl_config = config.get("db.ttl")
    match_keys = [ttl_name, "batch_size"]
    new_ttl_config = {k: ttl_config[k] for k in match_keys if k in ttl_config}
    tasks = determine_tasks(**new_ttl_config)
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


def determine_tasks(**kwargs) -> Tuple[List[dict], int]:
    """Determine tasks and run interval from TTL values

    Args:
        kwargs: TTL values for the different task types. Valid kwarg keys are:
            - info
            - action

    Returns:
        A tuple that contains:
            - A list of task configurations
            - The suggested interval between runs

    """
    info_ttl = kwargs.get("info", -1)
    action_ttl = kwargs.get("action", -1)
    file_ttl = kwargs.get("file", -1)
    admin_ttl = kwargs.get("admin", -1)
    temp_ttl = kwargs.get("temp", -1)
    batch_size = kwargs.get("batch_size", -1)

    prune_tasks = []
    if info_ttl > 0:
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=info_ttl),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & Q(command_type="INFO"),
            }
        )

    if action_ttl > 0:
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=action_ttl),
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

    if admin_ttl > 0:
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=admin_ttl),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & Q(command_type="ADMIN"),
            }
        )

    if temp_ttl > 0:
        prune_tasks.append(
            {
                "collection": Request,
                "batch_size": batch_size,
                "field": "created_at",
                "delete_after": timedelta(minutes=temp_ttl),
                "additional_query": (
                    Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                )
                & Q(has_parent=False)
                & Q(command_type="TEMP"),
            }
        )

    if file_ttl > 0:
        prune_tasks.append(
            {
                "collection": File,
                "batch_size": batch_size,
                "field": "updated_at",
                "delete_after": timedelta(minutes=file_ttl),
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
                "delete_after": timedelta(minutes=file_ttl),
            }
        )

    return prune_tasks


def prune_outstanding():
    """
    Helper function for run to mark requests still outstanding after a certain
    amount of time as canceled.
    """
    ttl_config = config.get("db.ttl")
    cancel_threshold = ttl_config.get("in_progress", -1)
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
