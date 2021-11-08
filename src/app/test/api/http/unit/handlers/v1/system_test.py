# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.events
import beer_garden.router
from beer_garden.api.http.authentication import generate_access_token
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
        name="permitted_system",
        version="0.0.1",
        namespace=garden.name,
        commands=[Command(name="icandoit")],
    ).save()

    yield system
    system.delete()


@pytest.fixture(autouse=True)
def system_not_permitted(garden):
    system = System(
        name="not_permitted_system",
        version="0.0.1",
        namespace=garden.name,
        commands=[Command(name="notallowed")],
    ).save()

    yield system
    system.delete()


@pytest.fixture
def system_admin_role():
    role = Role(
        name="system_admin",
        permissions=["system:create", "system:read", "system:update", "system:delete"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def system_cleanup():
    yield
    System.drop_collection()


@pytest.fixture
def user(system_permitted, system_admin_role):
    role_assignment = RoleAssignment(
        role=system_admin_role,
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
    yield generate_access_token(user)


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, system_permitted):
    def mock_determine_target(operation):
        return system_permitted.namespace

    def generic_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(beer_garden.events, "publish", generic_mock)
    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "forward", generic_mock)


class TestSystemAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_any_system(
        self, http_client, base_url, system_not_permitted
    ):
        url = f"{base_url}/api/v1/systems/{system_not_permitted.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(system_not_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_permitted,
    ):
        url = f"{base_url}/api/v1/systems/{system_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(system_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_returns_403_for_not_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_not_permitted,
    ):
        url = f"{base_url}/api/v1/systems/{system_not_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_auth_enabled_allows_delete_for_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_permitted,
    ):
        url = f"{base_url}/api/v1/systems/{system_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert len(System.objects.filter(id=system_permitted.id)) == 0

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_delete_for_not_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_not_permitted,
    ):
        url = f"{base_url}/api/v1/systems/{system_not_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert len(System.objects.filter(id=system_not_permitted.id)) == 1

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_permitted,
    ):
        url = f"{base_url}/api/v1/systems/{system_permitted.id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patch_body = [
            {"operation": "replace", "path": "/description", "value": "new description"}
        ]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert (
            System.objects.get(id=system_permitted.id).description == "new description"
        )

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_not_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_not_permitted,
    ):
        url = f"{base_url}/api/v1/systems/{system_not_permitted.id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patch_body = [
            {"operation": "replace", "path": "/description", "value": "new description"}
        ]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert (
            System.objects.get(id=system_not_permitted.id).description
            == system_not_permitted.description
        )


class TestSystemListAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_all_systems(self, http_client, base_url):
        url = f"{base_url}/api/v1/systems"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_systems(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        system_permitted,
    ):
        url = f"{base_url}/api/v1/systems"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 1
        assert response_body[0]["id"] == str(system_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_allows_post_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        garden,
        user,
        system_admin_role,
        system_cleanup,
    ):
        garden_role_assignment = RoleAssignment(
            role=system_admin_role,
            domain={"scope": "Garden", "identifiers": {"name": garden.name}},
        )
        user.role_assignments.append(garden_role_assignment)
        access_token = generate_access_token(user)

        url = f"{base_url}/api/v1/systems"
        headers = {"Authorization": f"Bearer {access_token}"}

        post_body = {
            "version": "1.0.0",
            "namespace": garden.name,
            "name": "newsystem",
            "commands": [
                {
                    "name": "mycommand",
                }
            ],
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(post_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 201
        assert len(System.objects.filter(name="newsystem", namespace=garden.name)) == 1

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_post_for_not_permitted_system(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        garden,
        access_token,
    ):
        url = f"{base_url}/api/v1/systems"
        headers = {"Authorization": f"Bearer {access_token}"}
        system_count_before = len(System.objects.all())

        post_body = {
            "version": "1.0.0",
            "namespace": "notpermitted",
            "name": "newsystem",
            "commands": [
                {
                    "name": "mycommand",
                }
            ],
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(post_body)
        )

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert len(System.objects.all()) == system_count_before
