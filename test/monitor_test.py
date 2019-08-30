import datetime
import unittest

from mock import MagicMock, Mock, patch

from bartender.monitor import PluginStatusMonitor


@patch("time.sleep", Mock())
class PluginStatusMonitorTest(unittest.TestCase):
    def setUp(self):
        instance_patcher = patch("bartender.monitor.Instance")
        self.addCleanup(instance_patcher.stop)
        self.instance_patch = instance_patcher.start()
        self.instance_patch.objects = []

        self.clients = MagicMock()
        self.monitor = PluginStatusMonitor(self.clients)

    @patch("bartender.monitor.PluginStatusMonitor.request_status")
    @patch("bartender.monitor.PluginStatusMonitor.check_status")
    def test_run_stopped(self, check_mock, request_mock):
        self.monitor._stop_event = Mock(wait=Mock(return_value=True))
        self.monitor.run()
        self.assertFalse(request_mock.called)
        self.assertFalse(check_mock.called)

    @patch("bartender.monitor.PluginStatusMonitor.request_status")
    @patch("bartender.monitor.PluginStatusMonitor.check_status")
    def test_run(self, check_mock, request_mock):
        self.monitor._stop_event = Mock(wait=Mock(side_effect=[False, True]))
        self.monitor.run()
        self.assertEqual(request_mock.call_count, 1)
        self.assertEqual(check_mock.call_count, 1)

    def test_request_status(self):
        self.monitor.request_status()
        expiration = str(self.monitor.heartbeat_interval * 1000)
        self.clients["pika"].publish_request.assert_called_once_with(
            self.monitor.status_request, routing_key="admin", expiration=expiration
        )

    def test_request_status_exception(self):
        self.clients["pika"].publish_request.side_effect = IOError
        self.monitor.request_status()
        expiration = str(self.monitor.heartbeat_interval * 1000)
        self.clients["pika"].publish_request.assert_called_once_with(
            self.monitor.status_request, routing_key="admin", expiration=expiration
        )

    @patch("bartender.monitor.PluginStatusMonitor.stopped")
    def test_check_status_empty(self, stopped_mock):
        self.monitor.check_status()
        self.assertFalse(stopped_mock.called)

    @patch("bartender.monitor.PluginStatusMonitor.stopped")
    def test_check_status_break_on_stop(self, stopped_mock):
        stopped_mock.return_value = True
        instance_mock = Mock(
            status="RUNNING", status_info={"heartbeat": datetime.datetime(2017, 1, 1)}
        )
        self.instance_patch.objects = [instance_mock]

        self.monitor.check_status()
        self.assertTrue(stopped_mock.called)

    @patch(
        "bartender.monitor.PluginStatusMonitor.stopped", Mock(side_effect=[False, True])
    )
    @patch(
        "bartender.monitor.datetime",
        Mock(utcnow=Mock(return_value=datetime.datetime(2017, 1, 1, second=45))),
    )
    def test_check_status_mark_as_unresponsive(self):
        instance_mock = Mock(
            status="RUNNING", status_info={"heartbeat": datetime.datetime(2017, 1, 1)}
        )
        self.instance_patch.objects = [instance_mock]

        self.monitor.check_status()
        self.assertEqual("UNRESPONSIVE", instance_mock.status)
        self.assertTrue(instance_mock.save.called)

    @patch(
        "bartender.monitor.PluginStatusMonitor.stopped", Mock(side_effect=[False, True])
    )
    @patch(
        "bartender.monitor.datetime",
        Mock(utcnow=Mock(return_value=datetime.datetime(2017, 1, 1))),
    )
    def test_check_status_mark_as_running(self):
        instance_mock = Mock(
            status="UNRESPONSIVE",
            status_info={"heartbeat": datetime.datetime(2017, 1, 1)},
        )
        self.instance_patch.objects = [instance_mock]

        self.monitor.check_status()
        self.assertEqual("RUNNING", instance_mock.status)
        self.assertTrue(instance_mock.save.called)
