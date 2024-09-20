import logging
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from brewtils.models import Event, Events, Replication
from brewtils.stoppable_thread import StoppableThread

import beer_garden
import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.events import publish_event

logger = logging.getLogger(__name__)


def get_replication_id() -> str:
    replication_id = os.environ.get("BG_REPLICATION_ID", None)

    if not replication_id:
        replication_id = str(uuid4())
        os.environ["BG_REPLICATION_ID"] = replication_id
    return replication_id


@publish_event(Events.REPLICATION_CREATED)
def create_replication(replication: Replication):
    return db.create(replication)


@publish_event(Events.REPLICATION_UPDATED)
def update_replication(replication: Replication):
    return db.update(replication)


def get_replications():
    return db.query(Replication)


class PrimaryReplicationMonitor(StoppableThread):
    """Monitor the Primary status of Replications"""

    def __init__(self, heartbeat_interval=10, timeout_seconds=30):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Primary Replication Status Monitor"
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timedelta(seconds=timeout_seconds)

        super(PrimaryReplicationMonitor, self).__init__(
            logger=self.logger, name="PrimaryReplicationMonitor"
        )

    def run(self):
        self.logger.debug(self.display_name + " is started")

        while not self.wait(self.heartbeat_interval):
            self.primary_check(self.timeout)

        self.logger.debug(self.display_name + " is stopped")

    def primary_check(self, timeout: timedelta) -> None:
        replication_id = get_replication_id()

        replications = get_replications()

        # Set self as Primary Replication
        if len(replications) == 0:
            if config.get("replication.enabled"):
                self.logger.info(
                    f"Setting to Primary Replication Instance {replication_id}"
                )
            create_replication(
                Replication(
                    replication_id=replication_id,
                    expires_at=datetime.now(timezone.utc) + timeout,
                )
            )

        # Check if Primary Replication
        elif len(replications) == 1:
            if replications[0].replication_id == replication_id:
                replications[0].expires_at = datetime.now(timezone.utc) + timeout
                update_replication(replications[0])

        # Two instances claimed Primary Replication, wait until one times out
        else:
            self.logger.error(
                f"Found {len(replications)} Instances as Primary Replication"
            )


def handle_event(event: Event) -> None:
    """Handle REPLICATION events

    BG should only handle events that are designated for the local environment. If BG
    triggers off a non-local Replication ID, then no schedulers will run

    Args:
        event: The event to handle
    """

    if event.garden == config.get("garden.name"):
        if event.name in [
            Events.REPLICATION_CREATED.name,
            Events.REPLICATION_UPDATED.name,
        ]:
            if event.payload.replication_id == get_replication_id():
                if not beer_garden.application.scheduler.running:
                    logger.debug("Starting Scheduler")
                    beer_garden.application.scheduler.start()
            elif beer_garden.application.scheduler.running:
                logger.debug("Stopping Scheduler")
                beer_garden.application.scheduler.shutdown(wait=False)
