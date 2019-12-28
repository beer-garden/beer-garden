import pytest

from beer_garden.local_plugins.monitor import LocalPluginMonitor
from beer_garden.local_plugins.manager import LocalPluginsManager, PluginRunner
from beer_garden.local_plugins.registry import LocalPluginRegistry


@pytest.fixture
def registry():
    return LocalPluginRegistry()


@pytest.fixture
def loader(validator, registry):
    return LocalPluginLoader(validator, registry)


@pytest.fixture
def manager(loader, validator, registry):
    return LocalPluginsManager(10)


@pytest.fixture
def monitor(manager, registry):
    return LocalPluginMonitor(manager)
