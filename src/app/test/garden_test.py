# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import System as BrewtilsSystem
from brewtils.specification import _CONNECTION_SPEC
from mongoengine import DoesNotExist, connect
from yapconf import YapconfSpec

from beer_garden import config
from beer_garden.db.mongo.models import Garden, RemoteUser, System
from beer_garden.garden import (
    create_garden,
    get_garden,
    get_gardens,
    local_garden,
    remove_garden,
)
from beer_garden.systems import create_system


@pytest.fixture(autouse=True)
def drop():
    yield
    Garden.drop_collection()
    System.drop_collection()


@pytest.fixture
def localgarden_system():
    yield create_system(
        BrewtilsSystem(
            name="localsystem", version="1.2.3", namespace="localgarden", local=True
        )
    )


@pytest.fixture
def localgarden(localgarden_system):
    yield create_garden(
        BrewtilsGarden(
            name="localgarden", connection_type="LOCAL", systems=[localgarden_system]
        )
    )


@pytest.fixture
def remotegarden_system():
    yield create_system(
        BrewtilsSystem(
            name="remotesystem", version="1.2.3", namespace="remotegarden", local=False
        )
    )


@pytest.fixture
def remotegarden(remotegarden_system):
    yield create_garden(
        BrewtilsGarden(
            name="remotegarden", connection_type="HTTP", systems=[remotegarden_system]
        )
    )


class TestGarden:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")
        config._CONFIG = {"garden": {"name": "localgarden"}}

    def test_get_garden(self, localgarden):
        """get_garden should allow for retrieval by name"""
        garden = get_garden(localgarden.name)

        assert type(garden) is BrewtilsGarden
        assert garden.name == localgarden.name

    def test_get_garden_raises_exception_when_not_found(self):
        """get_garden should raise DoesNotExist if no garden is found"""
        with pytest.raises(DoesNotExist):
            get_garden("notagarden")

    def test_get_gardens_includes_localgarden(self, localgarden, remotegarden):
        """get_gardens should include local gardens when requested"""
        gardens = get_gardens(include_local=True)

        assert len(gardens) == 2
        assert localgarden.name in [garden.name for garden in gardens]

    def test_get_gardens_excludes_localgarden(self, localgarden, remotegarden):
        """get_gardens should exclude local gardens when requested"""
        gardens = get_gardens(include_local=False)

        assert len(gardens) == 1
        assert localgarden.name != gardens[0].name

    def test_local_garden_returns_brewtils_model(self, localgarden):
        """local_garden returns a brewtils Garden"""
        garden = local_garden()

        assert type(garden) is BrewtilsGarden

    def test_local_garden_returns_all_systems(self, localgarden, remotegarden):
        """local_garden returns all systems (those of the local garden and its children)
        when requested"""
        garden = local_garden(all_systems=True)

        assert len(garden.systems) == 2

    def test_local_garden_returns_local_systems(self, localgarden, remotegarden):
        """local_garden returns local systems (those of the local garden only)
        when requested"""
        garden = local_garden(all_systems=False)

        assert len(garden.systems) == 1

    def test_remove_garden_removes_related_systems(self, localgarden, remotegarden):
        """remove_garden should also remove any systems of the garden"""
        remove_garden(remotegarden.name)

        # using len() instead of the QuerySet count() to silence pymongo warnings
        assert len(Garden.objects.filter(name=remotegarden.name)) == 0
        assert len(System.objects.filter(namespace=remotegarden.name)) == 0

        # confirm that systems of other gardens remain intact
        assert len(System.objects.filter(namespace=localgarden.name)) == 1

    def test_create_garden_loads_default_config(self, bg_garden):
        """create_garden should explicitly load default HTTP configs from brewtils"""

        http_params = {
            "host": "localhost",
            "port": 1337,
            "url_prefix": "/",
            "ssl": True,
            "ca_cert": "/abc",
            "ca_verify": True,
            "client_cert": "/def",
        }

        bg_garden.connection_params = {"http": http_params}

        garden = create_garden(bg_garden)
        for key in http_params:
            assert garden.connection_params["http"][key] == http_params[key]

    def test_create_garden_with_empty_connection_params(self, bg_garden):
        """create_garden should explicitly load default HTTP configs from brewtils when empty"""

        config_map = {
            "bg_host": "host",
            "bg_port": "port",
            "ssl_enabled": "ssl",
            "bg_url_prefix": "url_prefix",
            "ca_cert": "ca_cert",
            "ca_verify": "ca_verify",
            "client_cert": "client_cert",
        }

        spec = YapconfSpec(_CONNECTION_SPEC)
        # bg_host is required by brewtils garden spec
        defaults = spec.load_config({"bg_host": ""})

        garden = create_garden(bg_garden)
        for key in config_map:
            assert garden.connection_params["http"][config_map[key]] == defaults[key]

    def test_remove_garden_cleans_up_remote_user_entries(self, bg_garden):
        """remove_garden should remove any RemoteUser entries for that garden"""
        garden = create_garden(bg_garden)
        remote_user = RemoteUser(username="remoteuser", garden=garden.name).save()

        remove_garden(garden.name)

        remote_user_count = len(
            RemoteUser.objects.filter(username=remote_user.username, garden=garden.name)
        )

        assert remote_user_count == 0
