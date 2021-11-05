# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import generate_access_token
from beer_garden.db.mongo.models import Garden, Role, RoleAssignment, User
from beer_garden.log import PluginLoggingManager


@pytest.fixture(autouse=True)
def garden_permitted():
    garden = Garden(name="garden_permitted", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture
def garden_admin_role():
    role = Role(
        name="garden_admin",
        permissions=["garden:read", "garden:update"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user_with_permission(garden_permitted, garden_admin_role):
    role_assignment = RoleAssignment(
        role=garden_admin_role,
        domain={
            "scope": "Garden",
            "identifiers": {
                "name": garden_permitted.name,
            },
        },
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield generate_access_token(user_with_permission)


@pytest.fixture(autouse=True)
def logging_config(monkeypatch):
    remote_config = {"somekey": "somevalue"}
    monkeypatch.setattr(PluginLoggingManager, "_REMOTE_CONFIG", remote_config)

    yield remote_config


class TestLoggingAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_logging_config(
        self,
        http_client,
        base_url,
        logging_config,
    ):
        url = f"{base_url}/api/v1/logging/"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["somekey"] == logging_config["somekey"]

    @pytest.mark.gen_test
    def test_auth_enabled_logging_returns_results_for_user_with_permission(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_permitted,
        logging_config,
    ):
        url = f"{base_url}/api/v1/logging/"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["somekey"] == logging_config["somekey"]

    @pytest.mark.gen_test
    def test_auth_enabled_logging_returns_403_for_user_without_permission(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_not_permitted,
    ):
        url = f"{base_url}/api/v1/logging/"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403


class TestLoggingConfigAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_logging_config(
        self,
        http_client,
        base_url,
        logging_config,
    ):
        url = f"{base_url}/api/v1/config/logging/"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["somekey"] == logging_config["somekey"]

    @pytest.mark.gen_test
    def test_auth_enabled_logging_returns_results_for_user_with_permission(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_permitted,
        logging_config,
    ):
        url = f"{base_url}/api/v1/config/logging/"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["somekey"] == logging_config["somekey"]

    @pytest.mark.gen_test
    def test_auth_enabled_logging_returns_403_for_user_without_permission(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_not_permitted,
    ):
        url = f"{base_url}/api/v1/config/logging/"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403
