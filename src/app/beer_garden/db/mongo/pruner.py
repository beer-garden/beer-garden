# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from typing import List, Tuple

from brewtils.stoppable_thread import StoppableThread
from mongoengine import Q

from beer_garden.db.mongo.models import File, RawFile, Request


class MongoPruner(StoppableThread):
    """
    Class to prune Mongo DB canceled or timed out Request objects.

    Attributes:
        logger: Logger to run debug messages
        display_name: The name of the pruner
        run_every: How often to run the pruner in minutes
        tasks: List of tasks to prune
        cancel_threshold: Time after which outstanding requests are marked as canceled
                          in minutes
    """

    def __init__(self, tasks=None, run_every=None, cancel_threshold=None):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Mongo Pruner"
        self._run_every = (run_every or timedelta(minutes=15)).total_seconds()
        self._tasks = tasks or []
        self._cancel_threshold = cancel_threshold or -1

        super(MongoPruner, self).__init__(logger=self.logger, name="Remover")

    def add_task(
        self, collection=None, field=None, delete_after=None, additional_query=None
    ):
        """Adds tasks to pruner object"""
        self._tasks.append(
            {
                "collection": collection,
                "field": field,
                "delete_after": delete_after,
                "additional_query": additional_query,
            }
        )

    def _cancel_outstanding(self):
        """
        Helper function for run to mark requests still outstanding after a certain
        amount of time as canceled.
        """

        timeout = datetime.utcnow() - timedelta(minutes=self._cancel_threshold)
        outstanding_requests = Request.objects.filter(
            status__in=["IN_PROGRESS", "CREATED"], created_at__lte=timeout
        )
        for request in outstanding_requests:
            request.status = "CANCELED"
            request.save()

    def run(self):
        """Runs the pruner to delete tasks"""

        self.logger.debug(
            "%s is started with run interval %ss", self.display_name, self._run_every
        )

        while not self.wait(self._run_every):
            current_time = datetime.utcnow()

            for task in self._tasks:
                delete_older_than = current_time - task["delete_after"]

                query = Q(**{task["field"] + "__lt": delete_older_than})
                if task.get("additional_query", None):
                    query = query & task["additional_query"]

                self.logger.debug(
                    "Removing %ss older than %s"
                    % (task["collection"].__name__, str(delete_older_than))
                )
                task["collection"].objects(query).no_cache().delete()

            if self._cancel_threshold > 0:
                self._cancel_outstanding()

        self.logger.debug(self.display_name + " is stopped")

    @staticmethod
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

        prune_tasks = []
        if info_ttl > 0:
            prune_tasks.append(
                {
                    "collection": Request,
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
                    "field": "created_at",
                    "delete_after": timedelta(minutes=action_ttl),
                    "additional_query": (
                        Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                    )
                    & Q(has_parent=False)
                    & Q(command_type="ACTION"),
                }
            )

        if file_ttl > 0:
            prune_tasks.append(
                {
                    "collection": File,
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
                    "field": "created_at",
                    "delete_after": timedelta(minutes=file_ttl),
                }
            )

        # Look at the various TTLs to determine how often to run
        real_ttls = [x for x in kwargs.values() if x > 0]
        run_every = min(real_ttls) / 2 if real_ttls else None

        return prune_tasks, run_every
