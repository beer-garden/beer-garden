# -*- coding: utf-8 -*-
import json
from unittest.mock import Mock

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.router
from beer_garden.api.http.authentication import generate_access_token
from beer_garden.db.mongo.models import Garden, Role, RoleAssignment, User


@pytest.fixture(autouse=True)
def garden():
    garden = Garden(name="somegarden", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture
def garden_admin_role():
    role = Role(name="garden_admin", permissions=["garden:update"]).save()

    yield role
    role.delete()


@pytest.fixture
def user_with_permission(garden, garden_admin_role):
    role_assignment = RoleAssignment(
        role=garden_admin_role,
        domain={
            "scope": "Garden",
            "identifiers": {"name": garden.name},
        },
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield generate_access_token(user_with_permission)


@pytest.fixture
def rescan_mock():
    rescan_mock = Mock()
    rescan_mock.return_value = {}

    return rescan_mock


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, rescan_mock):
    route_functions = {
        "RUNNER_RESCAN": rescan_mock,
    }

    monkeypatch.setattr(beer_garden.router, "route_functions", route_functions)


class TestAdminAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_patch(self, http_client, base_url, rescan_mock):
        url = f"{base_url}/api/v1/admin"
        headers = {"Content-Type": "application/json"}
        patch_body = [{"operation": "rescan"}]

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert rescan_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_user_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_permitted,
        rescan_mock,
    ):
        url = f"{base_url}/api/v1/admin"
        headers = {
            "Authorization": f"Bearer {access_token_permitted}",
            "Content-Type": "application/json",
        }
        patch_body = [{"operation": "rescan"}]

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert rescan_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_user_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_not_permitted,
        rescan_mock,
    ):
        url = f"{base_url}/api/v1/admin"
        headers = {
            "Authorization": f"Bearer {access_token_not_permitted}",
            "Content-Type": "application/json",
        }
        patch_body = [{"operation": "rescan"}]

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert rescan_mock.called is False
