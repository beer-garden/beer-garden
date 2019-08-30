import logging
from datetime import datetime, timedelta

from mongoengine import Q

from brewtils.stoppable_thread import StoppableThread


class MongoPruner(StoppableThread):
    def __init__(self, tasks=None, run_every=timedelta(minutes=15)):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Mongo Pruner"
        self._run_every = run_every.total_seconds()
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
                task["collection"].objects(query).delete()

        self.logger.info(self.display_name + " is stopped")
