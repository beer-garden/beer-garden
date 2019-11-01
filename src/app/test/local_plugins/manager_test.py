# -*- coding: utf-8 -*-
import logging

import pytest
from brewtils.models import Instance, System
from mock import call, Mock

import beer_garden
from beer_garden.errors import PluginStartupError
from beer_garden.local_plugins.loader import LocalPluginLoader
from beer_garden.local_plugins.manager import LocalPluginsManager
from beer_garden.local_plugins.registry import LocalPluginRegistry
from beer_garden.local_plugins.validator import LocalPluginValidator


@pytest.fixture
def loader(monkeypatch):
    load = Mock()
    monkeypatch.setattr(LocalPluginLoader, "_instance", load)
    return load


@pytest.fixture
def validator(monkeypatch):
    val = Mock()
    monkeypatch.setattr(LocalPluginValidator, "_instance", val)
    return val


@pytest.fixture
def registry(monkeypatch, plugin, bg_system):
    reg = Mock(
        get_plugin=Mock(return_value=plugin),
        get_unique_plugin_names=Mock(return_value=[bg_system.name]),
        get_all_plugins=Mock(return_value=[plugin]),
        get_plugins_by_system=Mock(return_value=[plugin]),
    )
    monkeypatch.setattr(LocalPluginRegistry, "_instance", reg)
    return reg


@pytest.fixture
def pika_client():
    return Mock()


@pytest.fixture
def plugin(monkeypatch, bg_system):
    plug = Mock(
        system=bg_system,
        unique_name="unique_name",
        path_to_plugin="path/name-0.0.1",
        requirements=[],
        entry_point="main.py",
        plugin_args=[],
        instance_name="default",
        status="RUNNING",
    )

    monkeypatch.setattr(beer_garden.local_plugins.manager.db, "update", Mock())
    monkeypatch.setattr(
        beer_garden.local_plugins.manager.db, "query_unique", Mock(return_value=plug)
    )

    return plug


@pytest.fixture
def manager(loader, validator, registry, pika_client):
    return LocalPluginsManager({"pika": pika_client}, 1)


class TestStartPlugin(object):
    def test_initializing(self, manager, plugin):
        plugin.status = "INITIALIZING"
        assert manager.start_plugin(plugin) is True
        assert plugin.start.called is True
        assert plugin.status == "STARTING"

    def test_running(self, manager, plugin):
        assert manager.start_plugin(plugin) is True
        assert plugin.start.called is False

    def test_bad_status(self, manager, plugin):
        plugin.status = "BAD STATUS"
        with pytest.raises(PluginStartupError):
            manager.start_plugin(plugin)

        assert plugin.start.called is False

    def test_stopped(self, monkeypatch, manager, plugin, registry):
        plugin.status = "STOPPED"

        new_plugin = Mock()
        monkeypatch.setattr(
            beer_garden.local_plugins.manager,
            "LocalPluginRunner",
            Mock(return_value=new_plugin),
        )

        assert manager.start_plugin(plugin) is True

        assert plugin.status == "STARTING"
        assert plugin.start.called is False
        assert new_plugin.start.called is True

        registry.remove.assert_called_once_with(plugin.unique_name)
        registry.register_plugin.assert_called_once_with(new_plugin)


class TestStopPlugin(object):
    def test_running(self, manager, plugin, pika_client):
        plugin.is_alive.return_value = False

        manager.stop_plugin(plugin)
        assert plugin.status == "STOPPING"
        assert pika_client.publish_request.called is True
        assert plugin.stop.called is True
        assert plugin.join.called is True
        assert plugin.kill.called is False

    def test_stopped(self, manager, plugin, pika_client):
        plugin.is_alive.return_value = False
        plugin.status = "STOPPED"

        manager.stop_plugin(plugin)
        assert plugin.status == "STOPPED"
        assert pika_client.publish_request.called is False
        assert plugin.stop.called is False
        assert plugin.join.called is False
        assert plugin.kill.called is False

    def test_unknown(self, manager, plugin, pika_client):
        plugin.is_alive.return_value = False
        plugin.status = "UNKNOWN"

        manager.stop_plugin(plugin)
        assert plugin.status == "UNKNOWN"
        assert pika_client.publish_request.called is True
        assert plugin.stop.called is True
        assert plugin.join.called is True
        assert plugin.kill.called is False

    def test_exception(self, manager, plugin, pika_client):
        plugin.is_alive.return_value = True
        plugin.stop.side_effect = Exception()

        manager.stop_plugin(plugin)
        assert plugin.status == "DEAD"
        assert pika_client.publish_request.called is False
        assert plugin.stop.called is True
        assert plugin.join.called is False
        assert plugin.kill.called is True

    def test_unsuccessful(self, manager, plugin, pika_client):
        plugin.is_alive.return_value = True

        manager.stop_plugin(plugin)
        assert plugin.status == "DEAD"
        assert pika_client.publish_request.called is True
        assert plugin.stop.called is True
        assert plugin.join.called is True
        assert plugin.kill.called is True


class TestRestartPlugin(object):
    def test_restart(self, monkeypatch, manager, plugin):
        start_mock = Mock()
        stop_mock = Mock()
        monkeypatch.setattr(manager, "start_plugin", start_mock)
        monkeypatch.setattr(manager, "stop_plugin", stop_mock)

        manager.restart_plugin(plugin)
        assert stop_mock.called is True
        assert start_mock.called is True


class TestReloadSystem(object):
    def test_none(self, manager, registry, plugin):
        registry.get_plugins_by_system.return_value = []
        with pytest.raises(Exception):
            manager.reload_system(plugin.system.name, plugin.system.version)

    def test_fail_validation(self, manager, validator, plugin):
        validator.validate_plugin.return_value = False
        with pytest.raises(Exception):
            manager.reload_system(plugin.system.name, plugin.system.version)

    def test_running(self, manager, validator, plugin):
        validator.validate_plugin.return_value = True
        with pytest.raises(Exception):
            manager.reload_system(plugin.system.name, plugin.system.version)

    def test_stopped(self, manager, validator, registry, loader, plugin):
        plugin.status = "STOPPED"
        validator.validate_plugin.return_value = True

        manager.reload_system(plugin.system.name, plugin.system.version)
        registry.remove.assert_called_once_with(plugin.unique_name)
        loader.load_plugin.assert_called_once_with(plugin.path_to_plugin)


def test_start_all_plugins(monkeypatch, manager, plugin):
    start_mock = Mock()
    monkeypatch.setattr(manager, "_start_multiple_plugins", start_mock)

    manager.start_all_plugins()
    start_mock.assert_called_once_with([plugin])


class TestStartMultiple(object):
    @pytest.fixture(autouse=True)
    def mock_getter(self, monkeypatch, manager):
        monkeypatch.setattr(manager, "_get_all_system_names", Mock(return_value=[]))
        monkeypatch.setattr(manager, "_get_running_system_names", Mock(return_value=[]))
        monkeypatch.setattr(manager, "_get_failed_system_names", Mock(return_value=[]))

    @pytest.fixture
    def system_2(self):
        return System(name="system_name_2")

    @pytest.fixture
    def plugin_2(self, system_2):
        return Mock(
            system=system_2,
            unique_name="unique_name2",
            path_to_plugin="path/name-0.0.1",
            requirements=[],
            entry_point="main.py",
            plugin_args=[],
            instance_name="default2",
            status="RUNNING",
        )

    def test_empty(self, monkeypatch, manager):
        start_mock = Mock()
        monkeypatch.setattr(manager, "start_plugin", start_mock)

        manager._start_multiple_plugins([])
        assert start_mock.called is False

    def test_no_requirements(self, monkeypatch, manager, plugin, plugin_2, bg_system):
        start_mock = Mock()
        monkeypatch.setattr(manager, "start_plugin", start_mock)

        manager._start_multiple_plugins([plugin, plugin_2])
        start_mock.assert_has_calls([call(plugin), call(plugin_2)], any_order=True)

    def test_invalid_requirements(self, monkeypatch, manager, plugin):
        fail_mock = Mock()
        monkeypatch.setattr(manager, "_mark_as_failed", fail_mock)

        plugin.requirements = ["DNE"]

        manager._start_multiple_plugins([plugin])
        fail_mock.assert_called_once_with(plugin)

    def test_skip_first(
        self, monkeypatch, manager, bg_system, system_2, plugin, plugin_2
    ):
        start_mock = Mock()
        monkeypatch.setattr(manager, "start_plugin", start_mock)

        manager._get_all_system_names.return_value = [bg_system.name, system_2.name]

        plugin_2.requirements = [bg_system.name]

        manager._start_multiple_plugins([plugin, plugin_2])
        start_mock.assert_has_calls([call(plugin), call(plugin_2)], any_order=True)

    def test_requirement_already_running(
        self, monkeypatch, manager, bg_system, plugin_2
    ):
        start_mock = Mock()
        monkeypatch.setattr(manager, "start_plugin", start_mock)

        manager._get_all_system_names.return_value = [
            bg_system.name,
            plugin_2.system.name,
        ]
        manager._get_running_system_names.return_value = [bg_system.name]

        plugin_2.requirements = [bg_system.name]

        manager._start_multiple_plugins([plugin_2])
        start_mock.assert_has_calls([call(plugin_2)], any_order=True)

    def test_failed_requirement_start(
        self, monkeypatch, manager, bg_system, plugin, plugin_2
    ):
        start_mock = Mock(return_value=False)
        monkeypatch.setattr(manager, "start_plugin", start_mock)
        fail_mock = Mock()
        monkeypatch.setattr(manager, "_mark_as_failed", fail_mock)

        manager._get_all_system_names.return_value = [
            bg_system.name,
            plugin_2.system.name,
        ]

        plugin_2.requirements = [bg_system.name]

        manager._start_multiple_plugins([plugin, plugin_2])
        start_mock.assert_called_once_with(plugin)
        fail_mock.assert_called_once_with(plugin_2)


def test_get_all_system_names(monkeypatch, manager, bg_system):
    monkeypatch.setattr(
        beer_garden.local_plugins.manager.db, "query", Mock(return_value=[bg_system])
    )

    assert manager._get_all_system_names() == [bg_system.name]


class TestStopAllPlugins(object):
    def test_empty(self, monkeypatch, manager, registry, plugin):
        stop_mock = Mock()
        monkeypatch.setattr(manager, "stop_plugin", stop_mock)

        registry.get_all_plugins.return_value = []

        manager.stop_all_plugins()
        assert stop_mock.called is False

    def test_one_running(self, monkeypatch, manager, plugin):
        stop_mock = Mock()
        monkeypatch.setattr(manager, "stop_plugin", stop_mock)

        manager.stop_all_plugins()
        stop_mock.assert_called_once_with(plugin)

    def test_exception(self, monkeypatch, caplog, manager, registry, plugin):
        stop_mock = Mock(side_effect=[Exception(), None])
        monkeypatch.setattr(manager, "stop_plugin", stop_mock)

        registry.get_all_plugins.return_value = [plugin, plugin]

        with caplog.at_level(logging.WARNING):
            manager.stop_all_plugins()

        stop_mock.assert_has_calls([call(plugin), call(plugin)])
        assert len(caplog.records) == 2
        assert caplog.records[0].levelno == logging.ERROR
        assert caplog.records[1].levelno == logging.ERROR


class TestScanPluginPath(object):
    def test_no_change(self, monkeypatch, manager, loader, registry, plugin):
        monkeypatch.setattr(manager, "_start_multiple_plugins", Mock())

        loader.scan_plugin_path.return_value = [plugin.path_to_plugin]
        registry.get_all_plugins.return_value = [plugin]

        manager.scan_plugin_path()
        assert loader.load_plugin.called is False

    def test_one_new(self, monkeypatch, manager, loader, registry, plugin):
        start_mock = Mock()
        monkeypatch.setattr(manager, "_start_multiple_plugins", start_mock)

        loader.scan_plugin_path.return_value = [plugin.path_to_plugin]
        loader.load_plugin.return_value = [plugin]
        registry.get_all_plugins.return_value = []

        manager.scan_plugin_path()
        loader.load_plugin.assert_called_once_with(plugin.path_to_plugin)
        start_mock.assert_called_once_with([plugin])

    def test_two_new_could_not_load_one(
        self, monkeypatch, manager, loader, registry, plugin
    ):
        start_mock = Mock()
        monkeypatch.setattr(manager, "_start_multiple_plugins", start_mock)

        loader.scan_plugin_path.return_value = [plugin.path_to_plugin, "path/tw-0.0.1"]
        loader.load_plugin.side_effect = [[plugin], []]
        registry.get_all_plugins.return_value = []

        manager.scan_plugin_path()
        loader.load_plugin.assert_has_calls(
            [call(plugin.path_to_plugin), call("path/tw-0.0.1")], any_order=True
        )
        start_mock.assert_called_once_with([plugin])

    def test_one_exception(self, monkeypatch, manager, loader, registry, plugin):
        start_mock = Mock()
        monkeypatch.setattr(manager, "_start_multiple_plugins", start_mock)

        loader.scan_plugin_path.return_value = [plugin.path_to_plugin, "path/tw-0.0.1"]
        loader.load_plugin.side_effect = [[plugin], Exception()]
        registry.get_all_plugins.return_value = []

        manager.scan_plugin_path()
        loader.load_plugin.assert_has_calls(
            [call(plugin.path_to_plugin), call("path/tw-0.0.1")], any_order=True
        )
        start_mock.assert_called_once_with([plugin])


def test_mark_as_failed(monkeypatch, manager, plugin, bg_instance):
    bg_system_mock = Mock(instances=[bg_instance])

    monkeypatch.setattr(
        beer_garden.local_plugins.manager.db,
        "query_unique",
        Mock(return_value=bg_system_mock),
    )

    manager._mark_as_failed(plugin)
    assert bg_instance.status == "DEAD"


class TestGetFailedSystemNames(object):
    def test_one_failed(self, monkeypatch, manager, bg_system):
        bg_system.instances[0].status = "DEAD"

        monkeypatch.setattr(
            beer_garden.local_plugins.manager.db,
            "query",
            Mock(return_value=[bg_system]),
        )

        assert manager._get_failed_system_names() == [bg_system.name]

    def test_one_failed_one_running(self, monkeypatch, manager, bg_system):
        # Add one dead instance to system with one running one
        bg_system.instances.append(Instance(status="DEAD"))

        monkeypatch.setattr(
            beer_garden.local_plugins.manager.db,
            "query",
            Mock(return_value=[bg_system]),
        )

        assert manager._get_failed_system_names() == []
