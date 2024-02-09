# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
import os

from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Connection as BrewtilsConnection
from brewtils.models import System as BrewtilsSystem
from mongoengine import DoesNotExist, connect

from beer_garden import config
from beer_garden.db.mongo.models import Garden, RemoteUser, System
from beer_garden.garden import (
    create_garden,
    get_garden,
    get_gardens,
    local_garden,
    remove_garden,
    load_garden_connections,
    update_garden_receiving_heartbeat,
    update_garden_status,
    upsert_garden,
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
            name="remotegarden", connection_type="REMOTE", systems=[remotegarden_system]
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

    def test_create_garden_default_config(self, bg_garden):
        """create_garden set publishing connections to Missing Configuration when missing"""

        bg_garden.publishing_connections = []
        garden = create_garden(bg_garden)
        for connection in garden.publishing_connections:
            assert connection.status == "MISSING_CONFIGURATION"

    def test_load_configuration_file(self, bg_garden, tmpdir):
        """Loads a yaml file containing configuration details"""

        contents = """publishing: true
receiving: true
http:
  access_token: null
  api_version: 1
  client_timeout: -1
  enabled: true
  host: localhost
  password: null
  port: 2337
  refresh_token: null
  ssl:
    ca_cert: null
    ca_path: null
    ca_verify: true
    client_cert: null
    client_cert_verify: NONE
    client_key: null
    enabled: false
    private_key: null
    public_key: null
  url_prefix: /
  username: null
skip_events: []
stomp:
  enabled: false
  headers: []
  host: localhost
  password: password
  port: 61613
  send_destination: Beer_Garden_Operations_Parent
  ssl:
    ca_cert: null
    client_cert: null
    client_key: null
    use_ssl: false
  subscribe_destination: Beer_Garden_Forward_Parent
  username: beer_garden"""
        config_file = Path(tmpdir, "garden.yaml")
        with open(config_file, "w") as f:
            f.write(contents)

        config._CONFIG = {"children": {"directory": tmpdir}}

        garden = load_garden_connections(bg_garden)
        for connection in garden.publishing_connections:
            if connection.api == "HTTP":
                assert connection.status == "PUBLISHING"
            else:
                assert connection.status == "NOT_CONFIGURED"

        os.remove(config_file)

    def test_load_configuration_file_disabled_publishing(self, bg_garden, tmpdir):
        """Loads a yaml file containing configuration details"""

        contents = """publishing: false
receiving: true
http:
  access_token: null
  api_version: 1
  client_timeout: -1
  enabled: true
  host: localhost
  password: null
  port: 2337
  refresh_token: null
  ssl:
    ca_cert: null
    ca_path: null
    ca_verify: true
    client_cert: null
    client_cert_verify: NONE
    client_key: null
    enabled: false
    private_key: null
    public_key: null
  url_prefix: /
  username: null
skip_events: []
stomp:
  enabled: false
  headers: []
  host: localhost
  password: password
  port: 61613
  send_destination: Beer_Garden_Operations_Parent
  ssl:
    ca_cert: null
    client_cert: null
    client_key: null
    use_ssl: false
  subscribe_destination: Beer_Garden_Forward_Parent
  username: beer_garden"""
        config_file = Path(tmpdir, "garden.yaml")

        with open(config_file, "w") as f:
            f.write(contents)

        config._CONFIG = {"children": {"directory": tmpdir}}

        garden = load_garden_connections(bg_garden)
        for connection in garden.publishing_connections:
            if connection.api == "HTTP":
                assert connection.status == "DISABLED"
            else:
                assert connection.status == "NOT_CONFIGURED"

        os.remove(config_file)

    def test_load_configuration_file_disable_receiving(self, bg_garden, tmpdir):
        """Loads a yaml file containing configuration details"""

        contents = """publishing: true
receiving: false
http:
  access_token: null
  api_version: 1
  client_timeout: -1
  enabled: true
  host: localhost
  password: null
  port: 2337
  refresh_token: null
  ssl:
    ca_cert: null
    ca_path: null
    ca_verify: true
    client_cert: null
    client_cert_verify: NONE
    client_key: null
    enabled: false
    private_key: null
    public_key: null
  url_prefix: /
  username: null
skip_events: []
stomp:
  enabled: false
  headers: []
  host: localhost
  password: password
  port: 61613
  send_destination: Beer_Garden_Operations_Parent
  ssl:
    ca_cert: null
    client_cert: null
    client_key: null
    use_ssl: false
  subscribe_destination: Beer_Garden_Forward_Parent
  username: beer_garden"""
        config_file = Path(tmpdir, "garden.yaml")
        with open(config_file, "w") as f:
            f.write(contents)

        config._CONFIG = {"children": {"directory": tmpdir}}

        bg_garden.receiving_connections = [
            BrewtilsConnection(api="http", status="RECEIVING")
        ]

        garden = load_garden_connections(bg_garden)
        for connection in garden.receiving_connections:
            assert connection.status == "DISABLED"

        os.remove(config_file)

    def test_remove_garden_cleans_up_remote_user_entries(self, bg_garden):
        """remove_garden should remove any RemoteUser entries for that garden"""
        garden = create_garden(bg_garden)
        remote_user = RemoteUser(username="remoteuser", garden=garden.name).save()

        remove_garden(garden.name)

        remote_user_count = len(
            RemoteUser.objects.filter(username=remote_user.username, garden=garden.name)
        )

        assert remote_user_count == 0

    def test_update_garden_receiving_heartbeat_update_heartbeat(self):
        # New garden
        garden = update_garden_receiving_heartbeat("http", garden_name="new_garden")

        assert len(garden.receiving_connections) == 1
        assert garden.receiving_connections[0].status == "DISABLED"

    def test_update_garden_receiving_heartbeat_existing_garden_new_api_with_config(
        self, tmpdir, bg_garden
    ):
        # New garden

        bg_garden.systems = []

        garden = create_garden(bg_garden)
        assert len(garden.receiving_connections) == 1

        contents = """publishing: true
receiving: true
http:
  access_token: null
  api_version: 1
  client_timeout: -1
  enabled: true
  host: localhost
  password: null
  port: 2337
  refresh_token: null
  ssl:
    ca_cert: null
    ca_path: null
    ca_verify: true
    client_cert: null
    client_cert_verify: NONE
    client_key: null
    enabled: false
    private_key: null
    public_key: null
  url_prefix: /
  username: null
skip_events: []
stomp:
  enabled: false
  headers: []
  host: localhost
  password: password
  port: 61613
  send_destination: Beer_Garden_Operations_Parent
  ssl:
    ca_cert: null
    client_cert: null
    client_key: null
    use_ssl: false
  subscribe_destination: Beer_Garden_Forward_Parent
  username: beer_garden"""
        config_file = Path(tmpdir, f"{garden.name}.yaml")
        with open(config_file, "w") as f:
            f.write(contents)

        config._CONFIG = {"children": {"directory": tmpdir}}

        garden = update_garden_receiving_heartbeat("STOMP", garden_name=garden.name)

        assert len(garden.receiving_connections) == 2

        for connection in garden.receiving_connections:
            assert connection.status == "RECEIVING"

        os.remove(config_file)

    def test_update_garden_receiving_heartbeat_existing_garden_new_api(self, bg_garden):
        # New garden

        bg_garden.systems = []

        garden = create_garden(bg_garden)
        assert len(garden.receiving_connections) == 1

        garden = update_garden_receiving_heartbeat("STOMP", garden_name=garden.name)

        assert len(garden.receiving_connections) == 2

        for connection in garden.receiving_connections:
            if connection.api == "STOMP":
                assert connection.status == "DISABLED"
            else:
                assert connection.status == "RECEIVING"

    def test_update_garden_status_stopped(self, bg_garden):
        bg_garden.systems = []
        create_garden(bg_garden)
        garden = update_garden_status(bg_garden.name, "STOPPED")

        assert len(garden.receiving_connections) > 0
        assert len(garden.publishing_connections) > 0

        for connection in garden.receiving_connections:
            assert connection.status == "DISABLED"
        for connection in garden.publishing_connections:
            assert connection.status == "DISABLED"

    def test_update_garden_status_start(self, bg_garden):
        for connection in bg_garden.receiving_connections:
            connection.status = "DISABLED"
        for connection in bg_garden.publishing_connections:
            connection.status = "DISABLED"
        bg_garden.systems = []

        create_garden(bg_garden)
        garden = update_garden_status(bg_garden.name, "RUNNING")

        for connection in garden.receiving_connections:
            assert connection.status == "RECEIVING"
        for connection in garden.publishing_connections:
            assert connection.status == "PUBLISHING"

    def test_upsert_garden_add_children(self, bg_garden):
        bg_garden.systems = []

        bg_garden.children = [
            BrewtilsGarden(
                name="child",
                status="RUNNING",
                connection_type="REMOTE",
                has_parent=True,
                parent="garden",
            )
        ]

        upsert_garden(bg_garden)

        child = get_garden("child")
        parent = get_garden("garden")

        assert child.name == "child"
        assert len(parent.children) == 1

    def test_upsert_garden_update_values(self, bg_garden):
        bg_garden.systems = []
        bg_garden.has_parent = False
        bg_garden.status = "RUNNING"
        bg_garden.metadata = {"test": "test"}
        bg_garden.connection_type = "REMOTE"

        garden = create_garden(bg_garden)

        garden.has_parent = True
        garden.status = "STOPPED"
        garden.metadata = {"alt": "alt"}
        garden.connection_type = "LOCAL"

        updated_garden = upsert_garden(garden)

        # Not changed
        assert not updated_garden.has_parent
        assert updated_garden.connection_type == "REMOTE"

        # Changed
        assert updated_garden.metadata == {"alt": "alt"}
        assert updated_garden.status == "STOPPED"
