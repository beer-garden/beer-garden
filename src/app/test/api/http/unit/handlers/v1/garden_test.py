# -*- coding: utf-8 -*-
import json

import pytest
import tornado.web
from box import Box
from mongoengine import connect
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.events
import beer_garden.router
from beer_garden import config
from beer_garden.api.http.authentication import generate_access_token
from beer_garden.api.http.client import SerializeHelper
from beer_garden.api.http.handlers.v1.garden import GardenAPI, GardenListAPI
from beer_garden.db.mongo.models import Garden, Role, RoleAssignment, User

# TODO: Load this from conftest using the actual _setup_application call
application = tornado.web.Application(
    [
        (r"/api/v1/gardens/?", GardenListAPI),
        (r"/api/v1/gardens/(.*)/?", GardenAPI),
    ],
    client=SerializeHelper(),
)


@pytest.fixture
def app_config_auth_enabled(monkeypatch):
    app_config = Box(
        {
            "auth": {"enabled": True, "token_secret": "notsosecret"},
            "garden": {"name": "somegarden"},
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


@pytest.fixture
def app_config_auth_disabled(monkeypatch):
    app_config = Box(
        {
            "auth": {"enabled": False, "token_secret": "notsosecret"},
            "garden": {"name": "somegarden"},
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


@pytest.fixture(autouse=True)
def garden_permitted():
    garden = Garden(name="somegarden", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture(autouse=True)
def garden_not_permitted():
    garden = Garden(name="remotegarden", connection_type="HTTP").save()

    yield garden
    garden.delete()


@pytest.fixture
def garden_admin_role():
    role = Role(
        name="garden_admin",
        permissions=["garden:create", "garden:read", "garden:update", "garden:delete"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def garden_cleanup():
    yield
    Garden.drop_collection()


@pytest.fixture
def user(garden_permitted, garden_admin_role):
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
def access_token(user):
    yield generate_access_token(user)


@pytest.fixture
def app():
    return application


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, garden_permitted):
    def mock_determine_target(operation):
        return garden_permitted.name

    def generic_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(beer_garden.events, "publish", generic_mock)
    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "forward", generic_mock)


class TestGardenAPI:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_auth_disabled_returns_any_garden(
        self, http_client, app_config_auth_disabled, base_url, garden_not_permitted
    ):
        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(garden_not_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_garden(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        garden_permitted,
    ):
        url = f"{base_url}/api/v1/gardens/{garden_permitted.name}"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(garden_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_returns_403_for_not_permitted_garden(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        garden_not_permitted,
    ):
        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_permitted_garden(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        garden_permitted,
    ):
        url = f"{base_url}/api/v1/gardens/{garden_permitted.name}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patch_body = [{"operation": "RUNNING"}]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert Garden.objects.get(id=garden_permitted.id).status == "RUNNING"

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_not_permitted_garden(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        garden_not_permitted,
    ):
        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patch_body = [{"operation": "RUNNING"}]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert (
            Garden.objects.get(id=garden_not_permitted.id).status
            == garden_not_permitted.status
        )


class TestGardenListAPI:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_auth_disabled_returns_all_gardens(
        self, http_client, app_config_auth_disabled, base_url
    ):
        url = f"{base_url}/api/v1/gardens"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_gardens(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        garden_permitted,
    ):
        url = f"{base_url}/api/v1/gardens"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 1
        assert response_body[0]["id"] == str(garden_permitted.id)

    # TODO: Add tests for POST with and without permissions. As of this writing,
    #      There is no way have POST permission for Gardens.  Once that is implemented,
    #      tests should be added here.
