# -*- coding: utf-8 -*-
import asyncio
import json
from unittest.mock import Mock

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.router
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.api.http.handlers.v1.instance import InstanceLogAPI
from beer_garden.db.mongo.models import (
    Garden,
    Instance,
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
def system(garden):
    instance = Instance(name="instance")
    system = System(
        name="system",
        version="1.0.0",
        namespace=garden.name,
        instances=[instance],
    ).save()

    yield system
    system.delete()


@pytest.fixture
def system_admin_role():
    role = Role(
        name="system_admin", permissions=["system:read", "system:update", "queue:read"]
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user_with_permission(system, system_admin_role):
    role_assignment = RoleAssignment(
        role=system_admin_role,
        domain={
            "scope": "System",
            "identifiers": {
                "name": system.name,
                "namespace": system.namespace,
            },
        },
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield issue_token_pair(user_with_permission)["access"]


@pytest.fixture
def instance_function_mock():
    future = asyncio.Future()
    future.set_result({"id": "doesn't", "output": "matter"})
    instance_function = Mock()
    instance_function.return_value = future

    return instance_function


@pytest.fixture
def router_mocks(monkeypatch, instance_function_mock):
    route_functions = {
        "INSTANCE_DELETE": instance_function_mock,
        "INSTANCE_START": instance_function_mock,
        "QUEUE_READ_INSTANCE": instance_function_mock,
    }

    monkeypatch.setattr(beer_garden.router, "route_functions", route_functions)


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, system, instance_function_mock):
    def mock_determine_target(operation):
        return system.namespace

    def generic_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "forward", generic_mock)
    monkeypatch.setattr(
        InstanceLogAPI, "_generate_get_response", instance_function_mock
    )


class TestInstanceAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_get(self, http_client, base_url, system):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == instance_id

    @pytest.mark.gen_test
    def test_auth_enabled_allows_get_for_user_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        access_token_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == instance_id

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_get_for_user_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        access_token_not_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_auth_disabled_allows_delete(
        self,
        http_client,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"

        request = HTTPRequest(url, method="DELETE")
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_delete_for_user_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_delete_for_user_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_not_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert instance_function_mock.called is False

    @pytest.mark.gen_test
    def test_auth_disabled_allows_patch(
        self,
        http_client,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {"Content-Type": "application/json"}
        patch_body = {"operations": [{"operation": "start"}]}

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_user_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token_permitted}",
        }
        patch_body = {"operations": [{"operation": "start"}]}

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_user_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_not_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token_not_permitted}",
        }
        patch_body = {"operations": [{"operation": "start"}]}

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert instance_function_mock.called is False


class TestInstanceLogAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_get(
        self,
        http_client,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}/logs"

        response = yield http_client.fetch(url)

        assert response.code == 200
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_get_for_user_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}/logs"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)

        assert response.code == 200
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_get_for_user_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_not_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}/logs"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403
        assert instance_function_mock.called is False


class TestInstanceQueueAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_get(
        self,
        http_client,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}/queues"

        response = yield http_client.fetch(url)

        assert response.code == 200
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_get_for_user_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}/queues"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)

        assert response.code == 200
        assert instance_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_get_for_user_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        system,
        router_mocks,
        instance_function_mock,
        access_token_not_permitted,
    ):
        instance_id = str(system.instances[0].id)
        url = f"{base_url}/api/v1/instances/{instance_id}/queues"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403
        assert instance_function_mock.called is False
