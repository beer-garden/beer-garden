# -*- coding: utf-8 -*-
import pytest
from mock import Mock, patch

import beer_garden.monitor
from beer_garden.plugin import StatusMonitor


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

    def test_mark_as_unresponsive(
        self, monkeypatch, monitor, bg_system, bg_instance
    ):
        stopped_mock = Mock(side_effect=[False, True])
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        update_mock = Mock()
        monkeypatch.setattr(beer_garden.plugin, "update", update_mock)

        monkeypatch.setattr(
            beer_garden.plugin.db, "query", Mock(return_value=[bg_system])
        )

        monitor.check_status()
        assert update_mock.called is True

    def test_mark_as_running(
        self, monkeypatch, monitor, bg_system, bg_instance, ts_dt
    ):
        stopped_mock = Mock(side_effect=[False, True])
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        update_mock = Mock()
        monkeypatch.setattr(beer_garden.plugin, "update", update_mock)

        bg_instance.status = "UNRESPONSIVE"
        monkeypatch.setattr(
            beer_garden.plugin.db, "query", Mock(return_value=[bg_system])
        )

        monkeypatch.setattr(
            beer_garden.plugin,
            "datetime",
            Mock(utcnow=Mock(return_value=ts_dt)),
        )

        monitor.check_status()
        assert update_mock.called is True
