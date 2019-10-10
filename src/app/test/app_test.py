# -*- coding: utf-8 -*-
import unittest

import pytest
import requests.exceptions
from mock import MagicMock, Mock, patch

import beer_garden
from beer_garden.app import BartenderApp, HelperThread


@patch("beer_garden.app.time", Mock())
class BartenderAppTest(unittest.TestCase):
    def setUp(self):
        beer_garden.config.load([])
        beer_garden.log.load({"level": "INFO"})

        self.app = BartenderApp()
        self.thrift_server = Mock()
        self.queue_manager = Mock()
        self.local_monitor = Mock()
        self.status_monitor = Mock()
        self.plugin_manager = Mock()
        self.plugin_loader = Mock()
        self.clients = MagicMock()
        self.mongo_pruner = Mock()

    @patch("beer_garden.app.BartenderApp._shutdown")
    @patch("beer_garden.app.BartenderApp._startup")
    def test_run(self, startup_mock, shutdown_mock):
        self.app.helper_threads = []
        self.app.stopped = Mock(side_effect=[False, True])

        self.app.run()
        startup_mock.assert_called_once_with()
        shutdown_mock.assert_called_once_with()

    @patch("beer_garden.app.BartenderApp._shutdown", Mock())
    @patch("beer_garden.app.BartenderApp._startup", Mock())
    def test_helper_thread_restart(self):
        helper_mock = Mock()
        helper_mock.thread.is_alive.return_value = False
        self.app.helper_threads = [helper_mock]
        self.app.stopped = Mock(side_effect=[False, True])

        self.app.run()
        helper_mock.start.assert_called_once_with()

    @patch("beer_garden.app.BartenderApp._shutdown", Mock())
    def test_startup(self):
        self.app.stopped = Mock(return_value=True)
        self.app.thrift_server = self.thrift_server
        self.app.local_monitor = self.local_monitor
        self.app.status_monitor = self.status_monitor
        self.app.plugin_loader = self.plugin_loader
        self.app.clients = self.clients
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

    @pytest.mark.skip(reason="Event notification subsystem not complete")
    @patch("beer_garden.bv_client")
    def test_startup_notification_error(self, client_mock):
        self.app.plugin_manager = self.plugin_manager
        self.app.clients = self.clients
        self.app.helper_threads = []

        client_mock.publish_event.side_effect = requests.exceptions.ConnectionError

        self.app._startup()

    @patch("beer_garden.app.BartenderApp._startup", Mock())
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
    def test_shutdown_notification_error(self, client_mock):
        self.app.plugin_manager = self.plugin_manager
        self.app.clients = self.clients
        self.app.helper_threads = []

        client_mock.publish_event.side_effect = requests.exceptions.ConnectionError

        self.app._shutdown()


class HelperThreadTest(unittest.TestCase):
    def setUp(self):
        self.callable_mock = Mock()
        self.helper = HelperThread(self.callable_mock)

    def test_start(self):
        self.helper.start()
        self.assertTrue(self.callable_mock.called)
        self.assertIsNotNone(self.helper.thread)
        self.assertTrue(self.helper.thread.start.called)

    def test_stop_thread_alive_successful(self):
        self.helper.thread = Mock(is_alive=Mock(side_effect=[True, False]))

        self.helper.stop()
        self.assertTrue(self.helper.thread.stop.called)
        self.assertTrue(self.helper.thread.join.called)

    def test_stop_thread_alive_unsuccessful(self):
        self.helper.thread = Mock(is_alive=Mock(return_value=True))

        self.helper.stop()
        self.assertTrue(self.helper.thread.stop.called)
        self.assertTrue(self.helper.thread.join.called)

    def test_stop_thread_dead(self):
        self.helper.thread = Mock(is_alive=Mock(return_value=False))

        self.helper.stop()
        self.assertFalse(self.helper.thread.stop.called)
        self.assertFalse(self.helper.thread.join.called)
