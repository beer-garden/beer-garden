# -*- coding: utf-8 -*-
import pytest
from box import Box
from brewtils.models import Garden, System
from mock import Mock

import beer_garden.config as config
import beer_garden.garden
import beer_garden.router


@pytest.fixture(autouse=True)
def setup():
    beer_garden.router.garden_lookup = {}
    beer_garden.router.garden_connections = {}

    conf = Box(default_box=True)
    conf.garden.name = "parent"
    config.assign(conf)


@pytest.fixture
def p_sys_1():
    return System(namespace="p", name="sys", version="1")


@pytest.fixture
def p_sys_2():
    return System(namespace="p", name="sys", version="2")


@pytest.fixture
def c_sys_1():
    return System(namespace="c", name="sys", version="1")


@pytest.fixture
def c_sys_2():
    return System(namespace="c", name="sys", version="2")


@pytest.fixture
def p_garden(p_sys_1, p_sys_2):
    return Garden(
        name="parent", connection_type="local", systems=[str(p_sys_1), str(p_sys_2)]
    )


@pytest.fixture
def c_garden(c_sys_1, c_sys_2):
    return Garden(
        name="child", connection_type="http", systems=[str(c_sys_1), str(c_sys_2)]
    )


@pytest.fixture
def get_gardens_mock(monkeypatch):
    mock = Mock(return_value=[])
    monkeypatch.setattr(beer_garden.router, "get_gardens", mock)
    return mock


@pytest.fixture
def get_systems_mock(monkeypatch):
    mock = Mock(return_value=[])
    monkeypatch.setattr(beer_garden.router, "get_systems", mock)
    return mock


class TestSetupRouting:
    def test_all(
        self, get_gardens_mock, get_systems_mock, p_garden, c_garden, p_sys_1, p_sys_2
    ):
        get_gardens_mock.return_value = [p_garden, c_garden]
        get_systems_mock.return_value = [p_sys_1, p_sys_2]

        beer_garden.router.setup_routing()

        assert beer_garden.router.garden_lookup == {
            "p:sys-1": "parent",
            "p:sys-2": "parent",
            "c:sys-1": "child",
            "c:sys-2": "child",
        }

    def test_ignore_local(self, get_gardens_mock, get_systems_mock, p_garden, c_garden):
        """Systems in p_garden should be ignored"""
        get_gardens_mock.return_value = [p_garden, c_garden]

        beer_garden.router.setup_routing()

        assert beer_garden.router.garden_lookup == {
            "c:sys-1": "child",
            "c:sys-2": "child",
        }
