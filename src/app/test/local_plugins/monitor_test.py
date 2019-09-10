import unittest

from mock import Mock, PropertyMock, patch

from beer_garden.local_plugins.monitor import LocalPluginMonitor


@patch("time.sleep", Mock())
class LocalPluginMonitorTest(unittest.TestCase):
    def setUp(self):
        self.fake_system = Mock(version="0.0.1")
        type(self.fake_system).name = PropertyMock(return_value="plugin1")
        self.fake_plugin = Mock(
            system=self.fake_system,
            unique_name="plugin1[inst1]-0.0.1",
            instance_name="inst1",
            status="INITIALIZING",
        )

        self.manager = Mock()
        self.registry = Mock()
        self.monitor = LocalPluginMonitor(self.manager, self.registry)

    @patch("bartender.local_plugins.monitor.LocalPluginMonitor.monitor")
    def test_run_stopped(self, monitor_mock):
        self.monitor._stop_event = Mock(wait=Mock(return_value=True))
        self.monitor.run()
        self.assertFalse(monitor_mock.called)

    @patch("bartender.local_plugins.monitor.LocalPluginMonitor.monitor")
    def test_run_monitor_called(self, monitor_mock):
        self.monitor._stop_event = Mock(wait=Mock(side_effect=[False, True]))
        self.monitor.run()
        self.assertEqual(monitor_mock.call_count, 1)

    @patch("bartender.local_plugins.monitor.LocalPluginMonitor.stopped")
    def test_monitor_empty(self, stopped_mock):
        self.registry.get_all_plugins = Mock(return_value=[])
        self.monitor.monitor()
        self.assertFalse(stopped_mock.called)

    @patch(
        "bartender.local_plugins.monitor.LocalPluginMonitor.stopped",
        Mock(side_effect=[True]),
    )
    def test_monitor_stopped(self):
        fake_plugin = Mock()
        self.registry.get_all_plugins = Mock(return_value=[fake_plugin])
        self.monitor.monitor()
        self.assertFalse(fake_plugin.process.poll.called)

    def test_multiple_plugins_alive(self):
        fake_plugin_1 = Mock(
            system=self.fake_system,
            unique_name="plugin1[inst1]-0.0.1",
            instance_name="inst1",
            status="RUNNING",
            process=Mock(poll=Mock(return_value=None)),
        )
        fake_plugin_2 = Mock(
            system=self.fake_system,
            unique_name="plugin1[inst2]-0.0.1",
            instance_name="inst2",
            status="RUNNING",
            process=Mock(poll=Mock(return_value=None)),
        )
        self.registry.get_all_plugins = Mock(
            return_value=[fake_plugin_1, fake_plugin_2]
        )

        self.monitor.monitor()
        self.assertFalse(self.manager.restart_plugin.called)
        self.assertEqual(1, fake_plugin_1.process.poll.call_count)
        self.assertEqual(1, fake_plugin_2.process.poll.call_count)

    def test_do_restart(self):
        self.fake_plugin.status = "RUNNING"
        self.fake_plugin.process.poll.return_value = 1
        self.fake_plugin.stopped.return_value = False
        self.registry.get_all_plugins.return_value = [self.fake_plugin]

        self.monitor.monitor()
        self.manager.restart_plugin.assert_called_once_with(self.fake_plugin)
        self.assertEqual("DEAD", self.fake_plugin.status)

    def test_plugin_starting(self):
        self.fake_plugin.status = "STARTING"
        self.fake_plugin.process.poll.return_value = 1
        self.fake_plugin.stopped.return_value = False
        self.registry.get_all_plugins.return_value = [self.fake_plugin]

        self.monitor.monitor()
        self.assertFalse(self.manager.restart_plugin.called)
        self.assertEqual("DEAD", self.fake_plugin.status)

    def test_plugin_initializing(self):
        self.fake_plugin.process.poll.return_value = 1
        self.fake_plugin.stopped.return_value = False
        self.registry.get_all_plugins.return_value = [self.fake_plugin]

        self.monitor.monitor()
        self.assertFalse(self.manager.restart_plugin.called)

    def test_plugin_not_alive_but_stopped_manually(self):
        self.fake_plugin.status = "STOPPED"
        self.fake_plugin.process.poll.return_value = 1
        self.fake_plugin.stopped.return_value = True
        self.registry.get_all_plugins.return_value = [self.fake_plugin]

        self.monitor.monitor()
        self.assertFalse(self.manager.restart_plugin.called)

    def test_plugin_not_alive_but_being_stopped(self):
        self.fake_plugin.status = "RUNNING"
        self.fake_plugin.process.poll.return_value = 1
        self.fake_plugin.stopped.return_value = True
        self.registry.get_all_plugins.return_value = [self.fake_plugin]

        self.monitor.monitor()
        self.assertFalse(self.manager.restart_plugin.called)
