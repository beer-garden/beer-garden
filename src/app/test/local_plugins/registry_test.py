# -*- coding: utf-8 -*-
import pytest
from mock import Mock, PropertyMock
from pytest_lazyfixture import lazy_fixture

from beer_garden.local_plugins.registry import LocalPluginRegistry


@pytest.fixture
def system_1():
    sys1 = Mock(version="0.0.1")
    type(sys1).name = PropertyMock(return_value="plugin1")
    return sys1


@pytest.fixture
def system_2():
    sys2 = Mock(version="0.0.1")
    type(sys2).name = PropertyMock(return_value="plugin2")
    return sys2


@pytest.fixture
def plugin_1(system_1):
    return Mock(
        system=system_1,
        unique_name="plugin1[inst1]-0.0.1",
        instance_name="inst1",
        status="INITIALIZING",
    )


@pytest.fixture
def plugin_2(system_2):
    return Mock(
        system=system_2,
        unique_name="plugin2[inst1]-0.0.1",
        instance_name="inst1",
        status="INITIALIZING",
    )


@pytest.fixture
def plugin_3(system_2):
    return Mock(
        system=system_2,
        unique_name="plugin2[inst2]-0.0.1",
        instance_name="inst2",
        status="INITIALIZING",
    )


@pytest.fixture
def registry(plugin_1, plugin_2, plugin_3):
    registry = LocalPluginRegistry()
    registry._registry = [plugin_1, plugin_2, plugin_3]
    return registry


class TestRegistry(object):
    def test_get_all_plugins(self, registry, plugin_1, plugin_2, plugin_3):
        assert registry.get_all_plugins() == [plugin_1, plugin_2, plugin_3]

    def test_get_unique_plugin_names(self, registry):
        assert registry.get_unique_plugin_names() == {"plugin1", "plugin2"}

    @pytest.mark.parametrize(
        "name,plugin",
        [
            ("plugin1[inst1]-0.0.1", lazy_fixture("plugin_1")),
            ("plugin2[inst1]-0.0.1", lazy_fixture("plugin_2")),
            ("plugin2[inst2]-0.0.1", lazy_fixture("plugin_3")),
        ],
    )
    def test_get_plugin(self, registry, name, plugin):
        assert registry.get_plugin(name) == plugin

    def test_get_plugin_none(self, registry):
        assert registry.get_plugin("bad") is None

    def test_get_plugins_by_system_none(self, registry):
        assert registry.get_plugins_by_system("plugin3", "0.0.1") == []

    def test_get_plugins_by_system_one(self, registry, plugin_1):
        assert registry.get_plugins_by_system("plugin1", "0.0.1") == [plugin_1]

    def test_get_plugins_by_system_multiple(self, registry, plugin_2, plugin_3):
        assert registry.get_plugins_by_system("plugin2", "0.0.1") == [
            plugin_2,
            plugin_3,
        ]

    def test_remove(self, registry, plugin_1):
        registry.remove(plugin_1.unique_name)
        assert plugin_1 not in registry._registry
        assert len(registry._registry) == 2

    def test_remove_missing(self, registry):
        registry.remove("bad_name")
        assert len(registry._registry) == 3

    def test_register_plugin(self, registry, system_1):
        mock_plugin = Mock(
            system=system_1,
            unique_name="plugin1[inst2]-0.0.1",
            instance_name="inst2",
            status="INITIALIZING",
        )

        registry.register_plugin(mock_plugin)
        assert mock_plugin in registry._registry
        assert len(registry._registry) == 4

    def test_register_existing(self, registry, plugin_1):
        registry.register_plugin(plugin_1)
        assert plugin_1 in registry._registry
        assert len(registry._registry) == 3

    def test_plugin_exists_true(self, registry, system_1):
        exists = registry.plugin_exists(
            plugin_name=system_1.name, plugin_version=system_1.version
        )
        assert exists is True

    def test_plugin_exists_false(self, registry):
        exists = registry.plugin_exists(plugin_name="bad", plugin_version="0.0.1")
        assert exists is False

    def test_get_unique_name(self, registry):
        assert registry.get_unique_name("echo", "1.0", "default") == "echo[default]-1.0"
