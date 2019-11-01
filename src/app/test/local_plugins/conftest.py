import pytest
from mock import MagicMock

from beer_garden.local_plugins.loader import LocalPluginLoader
from beer_garden.local_plugins.manager import LocalPluginsManager
from beer_garden.local_plugins.monitor import LocalPluginMonitor
from beer_garden.local_plugins.registry import LocalPluginRegistry
from beer_garden.local_plugins.validator import LocalPluginValidator


@pytest.fixture
def registry():
    return LocalPluginRegistry()


@pytest.fixture
def validator():
    return LocalPluginValidator()


@pytest.fixture
def loader(validator, registry):
    return LocalPluginLoader(validator, registry)


@pytest.fixture
def manager(loader, validator, registry):
    return LocalPluginsManager(MagicMock(), 10)


@pytest.fixture
def monitor(manager, registry):
    return LocalPluginMonitor(manager)
