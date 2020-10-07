# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from typing import Tuple, List

from brewtils.stoppable_thread import StoppableThread
from mongoengine import Q

from beer_garden.db.mongo.models import Event, Request


class MongoPruner(StoppableThread):
    def __init__(self, tasks=None, run_every=None):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Mongo Pruner"
        self._run_every = (run_every or timedelta(minutes=15)).total_seconds()
        self._tasks = tasks or []

        super(MongoPruner, self).__init__(logger=self.logger, name="Remover")

    def add_task(
        self, collection=None, field=None, delete_after=None, additional_query=None
    ):
        self._tasks.append(
            {
                "collection": collection,
                "field": field,
                "delete_after": delete_after,
                "additional_query": additional_query,
            }
        )

    def run(self):
        self.logger.info(self.display_name + " is started")

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

        self.logger.info(self.display_name + " is stopped")

    @staticmethod
    def determine_tasks(**kwargs) -> Tuple[List[dict], int]:
        """Determine tasks and run interval from TTL values

        Args:
            kwargs: TTL values for the different task types. Valid kwarg keys are:
                - info
                - action
                - event

        Returns:
            A tuple that contains:
                - A list of task configurations
                - The suggested interval between runs

        """
        info_ttl = kwargs.get("info", -1)
        action_ttl = kwargs.get("action", -1)
        event_ttl = kwargs.get("event", -1)

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

        if event_ttl > 0:
            prune_tasks.append(
                {
                    "collection": Event,
                    "field": "timestamp",
                    "delete_after": timedelta(minutes=event_ttl),
                }
            )

        # Look at the various TTLs to determine how often to run
        real_ttls = [x for x in kwargs.values() if x > 0]
        run_every = min(real_ttls) / 2 if real_ttls else None

        return prune_tasks, run_every
