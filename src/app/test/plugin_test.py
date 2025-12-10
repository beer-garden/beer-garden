# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event, Events
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import System as BrewtilsSystem
from mock import Mock, patch

import beer_garden.monitor
from beer_garden.db.mongo.models import Garden, System, Topic
from beer_garden.plugin import StatusMonitor, handle_event
from beer_garden.systems import create_system


@pytest.fixture
def queue_mock(monkeypatch):
    queue = Mock()
    monkeypatch.setattr(beer_garden.plugin, "queue", queue)
    return queue


@pytest.fixture
def monitor():
    return StatusMonitor()


@patch("time.sleep", Mock())
class TestStatusMonitor(object):
    def test_run_stopped(self, monkeypatch, monitor):
        check_mock = Mock()
        request_mock = Mock()
        monkeypatch.setattr(monitor, "check_status", check_mock)
        monkeypatch.setattr(monitor, "request_status", request_mock)

        stop_mock = Mock(wait=Mock(return_value=True))
        monkeypatch.setattr(monitor, "_stop_event", stop_mock)

        monitor.run()

        assert check_mock.called is False
        assert request_mock.called is False

    def test_run(self, monkeypatch, monitor):
        check_mock = Mock()
        request_mock = Mock()
        monkeypatch.setattr(monitor, "check_status", check_mock)
        monkeypatch.setattr(monitor, "request_status", request_mock)

        stop_mock = Mock(wait=Mock(side_effect=[False, True]))
        monkeypatch.setattr(monitor, "_stop_event", stop_mock)

        monitor.run()

        assert check_mock.called is True
        assert request_mock.called is True

    def test_request_status(self, monitor, queue_mock):
        monitor.request_status()
        expiration = str(monitor.heartbeat_interval * 1000)

        queue_mock.put.assert_called_once_with(
            monitor.status_request, routing_key="admin", expiration=expiration
        )

    def test_request_status_exception(self, monitor, queue_mock):
        queue_mock.put.side_effect = IOError

        monitor.request_status()
        expiration = str(monitor.heartbeat_interval * 1000)
        queue_mock.put.assert_called_once_with(
            monitor.status_request, routing_key="admin", expiration=expiration
        )

    def test_break_on_stop(self, monkeypatch, monitor, bg_system):
        stopped_mock = Mock(return_value=True)
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        monkeypatch.setattr(
            beer_garden.plugin.db, "query", Mock(return_value=[bg_system])
        )

        monitor.check_status()
        assert stopped_mock.called is True

    def test_mark_as_unresponsive(self, monkeypatch, monitor, bg_system, bg_instance):
        stopped_mock = Mock(side_effect=[False, True])
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        update_mock = Mock()
        monkeypatch.setattr(beer_garden.plugin, "update", update_mock)

        monkeypatch.setattr(
            beer_garden.plugin.db, "query", Mock(return_value=[bg_system])
        )

        monitor.check_status()
        assert update_mock.called is True

    def test_mark_as_running(self, monkeypatch, monitor, bg_system, bg_instance, ts_dt):
        stopped_mock = Mock(side_effect=[False, True])
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        update_mock = Mock()
        monkeypatch.setattr(beer_garden.plugin, "update", update_mock)

        bg_instance.status = "UNRESPONSIVE"
        monkeypatch.setattr(
            beer_garden.plugin.db, "query", Mock(return_value=[bg_system])
        )

        monkeypatch.setattr(
            beer_garden.plugin, "datetime", Mock(now=Mock(return_value=ts_dt))
        )

        monitor.check_status()
        assert update_mock.called is True


class TestHandleEvent(object):

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test to ensure a clean state."""
        yield Garden(name="default", connection_type="LOCAL").save()
        System.drop_collection()
        Topic.drop_collection()
        Garden.drop_collection()

    @pytest.fixture
    def system(self):
        yield create_system(
            BrewtilsSystem(
                name="original",
                version="v0.0.0.dev0",
                namespace="beer_garden",
                garden_name="downstream_garden",
                local=True,
                commands=[],
                instances=[
                    BrewtilsInstance(
                        name="instance1",
                        status="RUNNING",
                    )
                ],
            )
        )

    def test_event_handler(
        self, system, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {"garden": {"name": "default"}}

        update_instance = system.instances[0]
        update_instance.status = "AWAITING_SYSTEM"

        event = Event(
            name=Events.INSTANCE_UPDATED.name,
            garden=system.garden_name,
            payload=update_instance,
            payload_type=BrewtilsInstance.__name__,
        )

        set_failed_event_manager()
        handle_event(event)
        updated_system = System.objects.get(id=system.id)
        updated_instance = updated_system.instances[0]
        assert updated_instance.status == "AWAITING_SYSTEM"

        # TODO: Fix handler from publishing events
        # check_failed_event_manager()
