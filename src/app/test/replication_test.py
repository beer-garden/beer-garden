import os
from datetime import datetime, timedelta, timezone

import pytest
from brewtils.models import Event, Events, Replication

import beer_garden
import beer_garden.config
from beer_garden.replication import (
    create_replication,
    get_replication_id,
    get_replications,
    handle_event,
    update_replication,
)


class TestReplication(object):

    @pytest.fixture
    def mock_scheduler(self):

        class MockScheduler(object):
            running = False

            def start(self):
                self.running = True

            def shutdown(self, wait=True):
                self.running = False

        class MockApplication(object):
            scheduler = None

        beer_garden.application = MockApplication()
        beer_garden.application.scheduler = MockScheduler()

    def test_get_replication_id(self):

        if "BG_REPLICATION_ID" in os.environ:
            del os.environ["BG_REPLICATION_ID"]

        replication_id = get_replication_id()

        assert replication_id == os.environ["BG_REPLICATION_ID"]

    def test_replication_expiration(self):
        create_replication(
            Replication(
                replication_id="1111",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
            )
        )

        assert len(get_replications()) == 0

    def test_update_replication(self):
        replication = create_replication(
            Replication(
                replication_id="1111",
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=100),
            )
        )

        replication.replication_id = "2222"
        update_replication(replication)

        db_replications = get_replications()
        assert len(db_replications) == 1
        assert db_replications[0].replication_id == "2222"

    def test_handle_event_set_primary(
        self, mock_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": True},
        }
        if "BG_REPLICATION_ID" in os.environ:
            del os.environ["BG_REPLICATION_ID"]

        os.environ["BG_REPLICATION_ID"] = "1111"
        replication = create_replication(
            Replication(
                replication_id="1111",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
            )
        )

        set_failed_event_manager()

        event = Event(
            payload=replication,
            name=Events.REPLICATION_CREATED.name,
            garden="default",
        )

        handle_event(event)
        assert beer_garden.application.scheduler.running
        check_failed_event_manager()

    def test_handle_event_not_primary(
        self, mock_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": True},
        }
        if "BG_REPLICATION_ID" in os.environ:
            del os.environ["BG_REPLICATION_ID"]

        os.environ["BG_REPLICATION_ID"] = "2222"
        replication = create_replication(
            Replication(
                replication_id="1111",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
            )
        )

        set_failed_event_manager()

        beer_garden.application.scheduler.running = True
        event = Event(
            payload=replication,
            name=Events.REPLICATION_CREATED.name,
            garden="default",
        )

        handle_event(event)
        assert not beer_garden.application.scheduler.running
        check_failed_event_manager()
