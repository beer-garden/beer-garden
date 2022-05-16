# -*- coding: utf-8 -*-
import json

import beer_garden.events
import beer_garden.router
import pytest
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import (
    Command,
    Garden,
    Role,
    RoleAssignment,
    System,
    User,
)
from beer_garden.systems import create_system
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import System as BrewtilsSystem
from tornado.httpclient import HTTPError, HTTPRequest


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
    yield issue_token_pair(user)["access"]


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, system_permitted):
    def mock_determine_target(operation):
        return system_permitted.namespace

    def generic_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(beer_garden.events, "publish", generic_mock)
    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "forward", generic_mock)


@pytest.fixture
def brewtils_system_with_instance():
    return BrewtilsSystem(
        name="system_with_instance",
        version="0.0.1",
        namespace="doesntmatter",
        commands=[BrewtilsCommand(name="notallowed")],
        instances=[
            BrewtilsInstance(
                name="instance1",
                queue_type="rabbit",
                queue_info={"supersecret": "shhh"},
            )
        ],
    )


@pytest.fixture
def system_with_instance(brewtils_system_with_instance):
    brewtils_system = create_system(brewtils_system_with_instance)
    system = System.objects.get(id=brewtils_system.id)

    yield system
    system.delete()


@pytest.fixture
def system_mock(monkeypatch, brewtils_system_with_instance):
    """Mocks the execute_local call that happens for operations returning a single
    System"""

    def mock_execute_local(operation):
        return brewtils_system_with_instance

    monkeypatch.setattr(beer_garden.router, "execute_local", mock_execute_local)


@pytest.fixture
def systems_mock(monkeypatch, brewtils_system_with_instance):
    """Mocks the execute_local call that happens for operations returning multiple
    Systems"""

    def mock_execute_local(operation):
        return [brewtils_system_with_instance]

    monkeypatch.setattr(beer_garden.router, "execute_local", mock_execute_local)


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

    @pytest.mark.gen_test
    def test_get_does_not_include_queue_info(
        self, http_client, base_url, system_with_instance
    ):
        url = f"{base_url}/api/v1/systems/{system_with_instance.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))
        instance = response_body["instances"][0]

        assert "queue_info" not in instance
        assert "queue_type" not in instance

    @pytest.mark.gen_test
    def test_patch_does_not_include_queue_info(
        self, http_client, base_url, system_with_instance, system_mock
    ):
        url = f"{base_url}/api/v1/systems/{system_with_instance.id}"
        headers = {
            "Content-Type": "application/json",
        }

        patch_body = [
            {"operation": "replace", "path": "/description", "value": "new description"}
        ]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)
        response_body = json.loads(response.body.decode("utf-8"))
        instance = response_body["instances"][0]

        assert "queue_info" not in instance
        assert "queue_type" not in instance


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
        access_token = issue_token_pair(user)["access"]

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

    @pytest.mark.gen_test
    def test_get_does_not_include_queue_info(self, http_client, base_url, systems_mock):
        url = f"{base_url}/api/v1/systems"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))
        instance = response_body[0]["instances"][0]

        assert "queue_info" not in instance
        assert "queue_type" not in instance
