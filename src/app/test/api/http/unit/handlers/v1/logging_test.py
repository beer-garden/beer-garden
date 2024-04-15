# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Garden
from beer_garden.log import PluginLoggingManager
from beer_garden.user import create_user, delete_user
from beer_garden.role import create_role, delete_role
from brewtils.models import User, Role

@pytest.fixture(autouse=True)
def garden_permitted():    
    garden = Garden(name="garden_permitted", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture
def garden_admin_role(garden_permitted):
    role = create_role(Role(name="garden_admin", permission="GARDEN_ADMIN", scope_gardens=[garden_permitted.name]))
    yield role
    delete_role(role)


@pytest.fixture
def user_with_permission(garden_admin_role):
    user = create_user(User(username="testuser", local_roles=[garden_admin_role]))
    yield user
    delete_user(user)


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield issue_token_pair(user_with_permission)["access"]


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
