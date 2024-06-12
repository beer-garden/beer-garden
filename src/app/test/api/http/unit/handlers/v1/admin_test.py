# -*- coding: utf-8 -*-
import json
from unittest.mock import Mock

import pytest
from brewtils.models import Garden, Role, User
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.db.api as db
import beer_garden.router
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.role import create_role, delete_role
from beer_garden.user import create_user, delete_user


@pytest.fixture(autouse=True)
def garden():
    garden = Garden(name="somegarden", connection_type="LOCAL")

    garden = db.create(garden)
    yield garden
    db.delete(garden)


@pytest.fixture
def garden_admin_role():
    role = Role(name="garden_admin", permission="GARDEN_ADMIN")

    role = create_role(role)
    yield role
    delete_role(role=role)


@pytest.fixture
def user_with_permission(garden, garden_admin_role):
    user = User(username="testuser", roles=["garden_admin"], password="password")

    user = create_user(user)
    yield user
    delete_user(user=user)


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield issue_token_pair(user_with_permission)["access"]


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

    # @pytest.mark.gen_test
    # def test_auth_enabled_rejects_patch_for_user_without_permission(
    #     self,
    #     http_client,
    #     app_config_auth_enabled,
    #     base_url,
    #     access_token_not_permitted,
    #     rescan_mock,
    # ):
    #     url = f"{base_url}/api/v1/admin"
    #     headers = {
    #         "Authorization": f"Bearer {access_token_not_permitted}",
    #         "Content-Type": "application/json",
    #     }
    #     patch_body = [{"operation": "rescan"}]

    #     request = HTTPRequest(
    #         url, method="PATCH", headers=headers, body=json.dumps(patch_body)
    #     )
    #     with pytest.raises(HTTPError) as excinfo:
    #         yield http_client.fetch(request)

    #     assert excinfo.value.code == 403
    #     assert rescan_mock.called is False
