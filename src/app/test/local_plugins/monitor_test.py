import pytest
from mock import Mock

from beer_garden.local_plugins.monitor import LocalPluginMonitor


@pytest.fixture
def manager():
    return Mock()


@pytest.fixture
def registry():
    return Mock()


@pytest.fixture
def monitor(manager, registry):
    return LocalPluginMonitor(manager, registry)


@pytest.fixture
def running_plugin():
    plug = Mock()
    plug.status = "RUNNING"
    plug.process.poll.return_value = 1
    plug.stopped.return_value = False
    return plug


@pytest.fixture
def stopped_plugin():
    plug = Mock()
    plug.status = "STOPPED"
    plug.process.poll.return_value = 1
    plug.stopped.return_value = True
    return plug


class TestLocalPluginMonitor(object):
    def test_run_call(self, monkeypatch, monitor):
        stop_mock = Mock(wait=Mock(side_effect=[False, True]))
        monitor_mock = Mock()
        monkeypatch.setattr(monitor, "_stop_event", stop_mock)
        monkeypatch.setattr(monitor, "monitor", monitor_mock)

        monitor.run()
        assert monitor_mock.call_count == 1

    def test_monitor_stopped(self, monkeypatch, monitor, registry):
        plugin = Mock()
        registry.get_all_plugins.return_value = [plugin]
        monkeypatch.setattr(monitor, "stopped", Mock(side_effect=[True]))

        monitor.monitor()
        assert plugin.process.poll.called is False

    def test_multiple_plugins_alive(self, monitor, registry, manager, bg_system):
        plugin_1 = Mock(
            system=bg_system,
            unique_name="plugin1[inst1]-0.0.1",
            instance_name="inst1",
            status="RUNNING",
            process=Mock(poll=Mock(return_value=None)),
        )
        plugin_2 = Mock(
            system=bg_system,
            unique_name="plugin1[inst2]-0.0.1",
            instance_name="inst2",
            status="RUNNING",
            process=Mock(poll=Mock(return_value=None)),
        )
        registry.get_all_plugins.return_value = [plugin_1, plugin_2]

        monitor.monitor()
        assert manager.restart_plugin.called is False
        assert plugin_1.process.poll.call_count == 1
        assert plugin_2.process.poll.call_count == 1

    def test_do_restart(self, monitor, registry, manager, running_plugin):
        registry.get_all_plugins.return_value = [running_plugin]

        monitor.monitor()
        manager.restart_plugin.assert_called_once_with(running_plugin)
        assert running_plugin.status == "DEAD"

    def test_plugin_starting(self, monitor, registry, manager, running_plugin):
        running_plugin.status = "STARTING"
        registry.get_all_plugins.return_value = [running_plugin]

        monitor.monitor()
        assert manager.restart_plugin.called is False
        assert running_plugin.status == "DEAD"

    def test_plugin_initializing(self, monitor, registry, manager, running_plugin):
        running_plugin.status = "INITIALIZING"
        registry.get_all_plugins.return_value = [running_plugin]

        monitor.monitor()
        assert manager.restart_plugin.called is False
        assert running_plugin.status == "INITIALIZING"

    def test_plugin_stopped_manually(self, monitor, registry, manager, stopped_plugin):
        registry.get_all_plugins.return_value = [stopped_plugin]

        monitor.monitor()
        assert manager.restart_plugin.called is False
        assert stopped_plugin.status == "STOPPED"

    def test_plugin_being_stopped(self, monitor, registry, manager, stopped_plugin):
        stopped_plugin.status = "RUNNING"
        registry.get_all_plugins.return_value = [stopped_plugin]

        monitor.monitor()
        assert manager.restart_plugin.called is False
        assert stopped_plugin.status == "RUNNING"
