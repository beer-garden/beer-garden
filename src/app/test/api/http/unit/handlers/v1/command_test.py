# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import (
    Command,
    Garden,
    Role,
    RoleAssignment,
    System,
    User,
)


@pytest.fixture
def garden():
    garden = Garden(name="somegarden", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture(autouse=True)
def system_permitted(garden):
    system = System(
        name="system_permitted",
        version="0.0.1",
        namespace=garden.name,
        commands=[Command(name="command_permitted")],
    ).save()

    yield system
    system.delete()


@pytest.fixture(autouse=True)
def system_not_permitted(garden):
    system = System(
        name="system_not_permitted",
        version="0.0.1",
        namespace=garden.name,
        commands=[Command(name="command_not_permitted")],
    ).save()

    yield system
    system.delete()


@pytest.fixture
def system_read_role():
    role = Role(
        name="system_admin",
        permissions=["system:read"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user(system_permitted, system_read_role):
    role_assignment = RoleAssignment(
        role=system_read_role,
        domain={
            "scope": "System",
            "identifiers": {
                "name": system_permitted.name,
                "namespace": system_permitted.namespace,
            },
        },
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def access_token(user):
    yield issue_token_pair(user)["access"]


class TestCommandAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_command_for_any_system(
        self, http_client, base_url, system_not_permitted
    ):
        command = system_not_permitted.commands[0]
        url = (
            f"{base_url}/api/v1/systems/{system_not_permitted.id}/commands/"
            f"{command.name}"
        )

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["name"] == command.name

    @pytest.mark.gen_test
    def test_auth_enabled_returns_command_for_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_permitted,
    ):
        command = system_permitted.commands[0]
        url = f"{base_url}/api/v1/systems/{system_permitted.id}/commands/{command.name}"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["name"] == command.name

    @pytest.mark.gen_test
    def test_auth_enabled_returns_403_for_not_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_not_permitted,
    ):
        command = system_not_permitted.commands[0]
        url = (
            f"{base_url}/api/v1/systems/{system_not_permitted.id}/commands/"
            f"{command.name}"
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403


class TestCommandListAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_commands_for_any_system(self, http_client, base_url):
        url = f"{base_url}/api/v1/commands/"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_returns_commands_for_permitted_systems(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_permitted,
    ):
        url = f"{base_url}/api/v1/commands/"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 1
        assert response_body[0]["name"] == system_permitted.commands[0].name
