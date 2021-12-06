# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Garden, Role, RoleAssignment, User


@pytest.fixture(autouse=True)
def garden():
    garden = Garden(name="somegarden", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture
def operation_data():
    yield {"operation_type": "GARDEN_READ", "garden_name": "somegarden"}


@pytest.fixture
def event_forward_role():
    role = Role(
        name="event_forward",
        permissions=["event:forward"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user_with_permission(event_forward_role):
    role_assignment = RoleAssignment(
        role=event_forward_role,
        domain={
            "scope": "Global",
        },
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def user_without_permission(event_forward_role):
    user = User(username="testuser").save()

    yield user
    user.delete()


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield issue_token_pair(user_with_permission)["access"]


@pytest.fixture
def access_token_not_permitted(user_without_permission):
    yield issue_token_pair(user_without_permission)["access"]


class TestGardenAPI:
    @pytest.mark.gen_test
    def test_auth_enabled_allows_forward_with_global_permission(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_permitted,
        operation_data,
    ):
        url = f"{base_url}/api/v1/forward/"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        request = HTTPRequest(
            url,
            method="POST",
            headers=headers,
            body=json.dumps(operation_data),
        )
        response = yield http_client.fetch(request)

        assert response.code == 204

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_forward_without_global_permission(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_not_permitted,
        operation_data,
    ):
        url = f"{base_url}/api/v1/forward/"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(operation_data)
        )

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
