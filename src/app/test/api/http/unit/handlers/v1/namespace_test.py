# -*- coding: utf-8 -*-
import json

import pytest
from brewtils.models import Role, User

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Garden
from beer_garden.role import create_role, delete_role
from beer_garden.user import create_user, delete_user


@pytest.fixture(autouse=True)
def garden_not_permitted():
    garden = Garden(
        name="notpermitted",
        connection_type="HTTP",
        has_parent=True,
        namespaces=["notpermitted"],
    ).save()

    yield garden
    garden.delete()


@pytest.fixture(autouse=True)
def garden_permitted(garden_not_permitted):
    garden = Garden(
        name="somegarden",
        connection_type="LOCAL",
        children=[garden_not_permitted],
        namespaces=["somegarden"],
    ).save()

    yield garden
    garden.delete()


@pytest.fixture
def garden_read_role(garden_permitted):
    role = create_role(
        Role(
            name="garden_read",
            permission="READ_ONLY",
            scope_gardens=[garden_permitted.name],
        )
    )
    yield role
    delete_role(role)


@pytest.fixture
def user_with_permission(garden_read_role):
    user = create_user(User(username="testuser", local_roles=[garden_read_role]))
    yield user
    delete_user(user=user)


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield issue_token_pair(user_with_permission)["access"]


class TestGardenAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_namespaces(
        self,
        http_client,
        base_url,
        garden_permitted,
        garden_not_permitted,
    ):
        url = f"{base_url}/api/v1/namespaces/"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_namespaces(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token_permitted,
        garden_permitted,
        garden_not_permitted,
    ):
        url = f"{base_url}/api/v1/namespaces/"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert garden_permitted.name in response_body
        assert garden_not_permitted.name not in response_body
