# -*- coding: utf-8 -*-
import pytest
from box import Box
from brewtils.models import Garden, System
from brewtils.test.comparable import assert_garden_equal
from mock import Mock

import beer_garden.config as config
import beer_garden.garden
import beer_garden.router


@pytest.fixture(autouse=True)
def setup():
    beer_garden.router.gardens = {}

    conf = Box(default_box=True)
    conf.garden.name = "parent"
    config.assign(conf, force=True)


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
def l_garden():
    return Garden(
        name="parent",
        connection_type="local",
        systems=[]
        # name="parent", connection_type="local", systems=[str(p_sys_1), str(p_sys_2)]
    )


@pytest.fixture
def p_garden(p_sys_1, p_sys_2):
    return Garden(name="parent", connection_type="local", systems=[p_sys_1, p_sys_2])


@pytest.fixture
def c_garden(c_sys_1, c_sys_2):
    return Garden(name="child", connection_type="http", systems=[c_sys_1, c_sys_2])


@pytest.fixture
def get_gardens_mock(monkeypatch):
    mock = Mock(return_value=[])
    monkeypatch.setattr(beer_garden.router, "get_gardens", mock)
    return mock


@pytest.fixture
def get_local_garden_mock(monkeypatch):
    mock = Mock(return_value=[])
    monkeypatch.setattr(beer_garden.router, "local_garden", mock)
    return mock


@pytest.mark.skip
class TestSetupRouting:
    def test_all(self, get_gardens_mock, get_local_garden_mock, p_garden, c_garden):
        get_gardens_mock.return_value = [c_garden]
        get_local_garden_mock.return_value = p_garden

        beer_garden.router.setup_routing()

        assert str(c_garden) in beer_garden.router.gardens
        assert str(p_garden) in beer_garden.router.gardens

        assert_garden_equal(c_garden, beer_garden.router.gardens[str(c_garden)])
        assert_garden_equal(p_garden, beer_garden.router.gardens[str(p_garden)])

    def test_ignore_local(
        self, get_gardens_mock, get_local_garden_mock, l_garden, c_garden
    ):
        """Systems in p_garden should be ignored"""
        get_gardens_mock.return_value = [c_garden]
        get_local_garden_mock.return_value = l_garden

        beer_garden.router.setup_routing()

        assert str(c_garden) in beer_garden.router.gardens
        assert str(l_garden) in beer_garden.router.gardens

        assert_garden_equal(c_garden, beer_garden.router.gardens[str(c_garden)])

        # "l_garden" is the local garden so it shouldn't have any systems
        assert not beer_garden.router.gardens[str(l_garden)].systems
