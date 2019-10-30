# -*- coding: utf-8 -*-
import pytest
from mock import Mock, patch

import beer_garden.monitor
from beer_garden.monitor import PluginStatusMonitor


@pytest.fixture
def pika_client():
    return Mock()


@pytest.fixture
def monitor(pika_client):
    return PluginStatusMonitor({"pika": pika_client})


@patch("time.sleep", Mock())
class TestPluginStatusMonitor(object):
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

    def test_request_status(self, monitor, pika_client):
        monitor.request_status()
        expiration = str(monitor.heartbeat_interval * 1000)

        pika_client.publish_request.assert_called_once_with(
            monitor.status_request, routing_key="admin", expiration=expiration
        )

    def test_request_status_exception(self, monitor, pika_client):
        pika_client.publish_request.side_effect = IOError

        monitor.request_status()
        expiration = str(monitor.heartbeat_interval * 1000)
        pika_client.publish_request.assert_called_once_with(
            monitor.status_request, routing_key="admin", expiration=expiration
        )

    def test_break_on_stop(self, monkeypatch, monitor, bg_instance):
        stopped_mock = Mock(return_value=True)
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        monkeypatch.setattr(
            beer_garden.monitor.db, "query", Mock(return_value=[bg_instance])
        )

        monitor.check_status()
        assert stopped_mock.called is True

    def test_mark_as_unresponsive(self, monkeypatch, monitor, bg_instance):
        stopped_mock = Mock(side_effect=[False, True])
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        update_mock = Mock()
        monkeypatch.setattr(beer_garden.monitor.db, "update", update_mock)

        monkeypatch.setattr(
            beer_garden.monitor.db, "query", Mock(return_value=[bg_instance])
        )

        monitor.check_status()
        assert bg_instance.status == "UNRESPONSIVE"
        assert update_mock.called is True

    def test_mark_as_running(self, monkeypatch, monitor, bg_instance, ts_dt):
        stopped_mock = Mock(side_effect=[False, True])
        monkeypatch.setattr(monitor, "stopped", stopped_mock)

        update_mock = Mock()
        monkeypatch.setattr(beer_garden.monitor.db, "update", update_mock)

        bg_instance.status = "UNRESPONSIVE"
        monkeypatch.setattr(
            beer_garden.monitor.db, "query", Mock(return_value=[bg_instance])
        )

        monkeypatch.setattr(
            beer_garden.monitor, "datetime", Mock(utcnow=Mock(return_value=ts_dt))
        )

        monitor.check_status()
        assert bg_instance.status == "RUNNING"
        assert update_mock.called is True
