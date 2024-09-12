# -*- coding: utf-8 -*-
import logging

import pytest
import requests.exceptions
from mock import Mock, call, patch

import beer_garden
from beer_garden.app import Application, HelperThread


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(beer_garden.app.Application, "initialize", Mock())
    return Application()


@pytest.mark.skip(reason="These tests are all mock-and-call")
@patch("beer_garden.app.time", Mock())
class TestApplication(object):
    @patch("beer_garden.app.Application._shutdown")
    @patch("beer_garden.app.Application._startup")
    def test_run(self, app, startup_mock, shutdown_mock):
        app.helper_threads = []
        app.stopped = Mock(side_effect=[False, True])

        app.run()
        startup_mock.assert_called_once_with()
        shutdown_mock.assert_called_once_with()

    @patch("beer_garden.app.Application._shutdown", Mock())
    @patch("beer_garden.app.Application._startup", Mock())
    def test_helper_thread_restart(self):
        helper_mock = Mock()
        helper_mock.thread.is_alive.return_value = False
        self.app.helper_threads = [helper_mock]
        self.app.stopped = Mock(side_effect=[False, True])

        self.app.run()
        helper_mock.start.assert_called_once_with()

    @patch("beer_garden.app.Application._shutdown", Mock())
    @patch("beer_garden.app.Application._setup_database", Mock())
    @patch("beer_garden.app.Application._setup_queues", Mock())
    def test_startup(self):
        self.app.stopped = Mock(return_value=True)
        self.app.thrift_server = self.thrift_server
        self.app.local_monitor = self.local_monitor
        self.app.status_monitor = self.status_monitor
        self.app.plugin_loader = self.plugin_loader
        self.app.plugin_manager = self.plugin_manager
        self.app.queue_manager = self.queue_manager
        self.app.helper_threads = [
            self.mongo_pruner,
            self.thrift_server,
            self.local_monitor,
            self.status_monitor,
        ]

        self.app.run()
        self.app.plugin_loader.load_plugins.assert_called_once_with()
        self.app.plugin_manager.start_all_plugins.assert_called_once_with()

        for helper in self.app.helper_threads:
            helper.start.assert_called_once_with()

    @patch("beer_garden.app.Application._startup", Mock())
    def test_shutdown(self):
        self.app.stopped = Mock(return_value=True)
        self.app.plugin_manager = self.plugin_manager
        self.app.helper_threads = [
            self.mongo_pruner,
            self.thrift_server,
            self.local_monitor,
            self.status_monitor,
        ]

        self.app.run()
        self.plugin_manager.stop_all_plugins.assert_called_once_with()

        for helper in self.app.helper_threads:
            helper.stop.assert_called_once_with()

    @pytest.mark.skip(reason="Event notification subsystem not complete")
    @patch("beer_garden.bv_client")
    def test_startup_notification_error(self, client_mock):
        self.app.plugin_manager = self.plugin_manager
        self.app.clients = self.clients
        self.app.helper_threads = []

        client_mock.publish_event.side_effect = requests.exceptions.ConnectionError

        self.app._startup()

    @pytest.mark.skip(reason="Event notification subsystem not complete")
    @patch("beer_garden.bv_client")
    def test_shutdown_notification_error(self, client_mock):
        self.app.plugin_manager = self.plugin_manager
        self.app.clients = self.clients
        self.app.helper_threads = []

        client_mock.publish_event.side_effect = requests.exceptions.ConnectionError

        self.app._shutdown()


class TestProgressiveBackoff(object):
    def test_increments(self, monkeypatch, app):
        func_mock = Mock(side_effect=[False, False, False, True])

        wait_mock = Mock()
        monkeypatch.setattr(app, "wait", wait_mock)

        app._progressive_backoff(func_mock, "test_func")
        wait_mock.assert_has_calls([call(0.1), call(0.2), call(0.4)])

    def test_max_timeout(self, monkeypatch, app):
        side_effect = [False] * 15
        side_effect[-1] = True
        func_mock = Mock(side_effect=side_effect)

        wait_mock = Mock()
        monkeypatch.setattr(app, "wait", wait_mock)

        app._progressive_backoff(func_mock, "test_func")
        max_val = max([mock_call[0][0] for mock_call in wait_mock.call_args_list])
        assert max_val == 30


class TestHelperThread(object):
    @pytest.fixture
    def callable_mock(self):
        return Mock()

    @pytest.fixture
    def helper(self, callable_mock):
        return HelperThread(callable_mock)

    def test_start(self, helper, callable_mock):
        helper.start()
        assert callable_mock.called is True
        assert helper.thread.start.called is True

    def test_stop_never_started(self, caplog, helper):
        with caplog.at_level(logging.DEBUG):
            helper.stop()

        assert len(caplog.records) == 0

    def test_stop_thread_alive_successful(self, caplog, helper):
        helper.thread = Mock(is_alive=Mock(side_effect=[True, False]))

        with caplog.at_level(logging.DEBUG):
            helper.stop()

        assert helper.thread.stop.called is True
        assert helper.thread.join.called is True
        assert caplog.records[-1].levelname == "DEBUG"

    def test_stop_thread_alive_unsuccessful(self, caplog, helper):
        helper.thread = Mock(is_alive=Mock(return_value=True))

        with caplog.at_level(logging.DEBUG):
            helper.stop()

        assert helper.thread.stop.called is True
        assert helper.thread.join.called is True
        assert caplog.records[-1].levelname == "WARNING"

    def test_stop_thread_dead(self, caplog, helper):
        helper.thread = Mock(is_alive=Mock(return_value=False))

        with caplog.at_level(logging.DEBUG):
            helper.stop()

        assert helper.thread.stop.called is False
        assert helper.thread.join.called is False
        assert caplog.records[-1].levelname == "WARNING"
