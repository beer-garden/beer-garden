# -*- coding: utf-8 -*-
from unittest.mock import Mock

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.router
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Garden
from beer_garden.user import create_user, delete_user
from beer_garden.role import create_role, delete_role
from brewtils.models import User, Role


@pytest.fixture(autouse=True)
def garden_permitted():
    garden = Garden(
        name="somegarden", connection_type="LOCAL", namespaces=["somegarden"]
    ).save()

    yield garden
    garden.delete()


@pytest.fixture
def queue_manager_role(garden_permitted):
    role = create_role(
        Role(
            name="queue_manager",
            permission="PLUGIN_ADMIN",
            scope_gardens=[garden_permitted.name],
        )
    )
    yield role
    delete_role(role)


@pytest.fixture
def user_with_permission(queue_manager_role):
    user = create_user(User(username="testuser", local_roles=[queue_manager_role]))
    yield user
    delete_user(user=user)


@pytest.fixture
def access_token_permitted(user_with_permission):
    yield issue_token_pair(user_with_permission)["access"]


@pytest.fixture
def queue_function_mock():
    queue_function = Mock()
    queue_function.return_value = {}

    return queue_function


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, garden_permitted, queue_function_mock):
    def mock_determine_target(operation):
        return garden_permitted.name

    route_functions = {
        "QUEUE_READ": queue_function_mock,
        "QUEUE_DELETE": queue_function_mock,
        "QUEUE_DELETE_ALL": queue_function_mock,
        "QUEUE_READ_INSTANCE": queue_function_mock,
    }

    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "route_functions", route_functions)


class TestQueueAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_delete(
        self, http_client, base_url, queue_function_mock
    ):
        url = f"{base_url}/api/v1/queues/somequeue"

        request = HTTPRequest(url, method="DELETE")
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert queue_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_delete_with_permissions(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_permitted,
        queue_function_mock,
    ):
        url = f"{base_url}/api/v1/queues/somequeue"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert queue_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_delete_without_permissions(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_not_permitted,
        queue_function_mock,
    ):
        url = f"{base_url}/api/v1/queues/somequeue"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert queue_function_mock.called is False

    @pytest.mark.gen_test
    def test_delete_works_with_special_characters(
        self, http_client, base_url, queue_function_mock
    ):
        url = f"{base_url}/api/v1/queues/some->queue"

        request = HTTPRequest(url, method="DELETE")
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert queue_function_mock.called is True


class TestQueueListAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_get(self, http_client, base_url, queue_function_mock):
        url = f"{base_url}/api/v1/queues/"

        response = yield http_client.fetch(url)

        assert response.code == 200
        assert queue_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_get_with_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_permitted,
        queue_function_mock,
    ):
        url = f"{base_url}/api/v1/queues/"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        response = yield http_client.fetch(url, headers=headers)

        assert response.code == 200
        assert queue_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_get_without_permission(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_not_permitted,
        queue_function_mock,
    ):
        url = f"{base_url}/api/v1/queues/"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403
        assert queue_function_mock.called is False

    @pytest.mark.gen_test
    def test_auth_disabled_allows_delete(
        self, http_client, base_url, queue_function_mock
    ):
        url = f"{base_url}/api/v1/queues/"

        request = HTTPRequest(url, method="DELETE")
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert queue_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_delete_with_permissions(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_permitted,
        queue_function_mock,
    ):
        url = f"{base_url}/api/v1/queues/"
        headers = {"Authorization": f"Bearer {access_token_permitted}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        response = yield http_client.fetch(request)

        assert response.code == 204
        assert queue_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_delete_without_permissions(
        self,
        http_client,
        app_config_auth_enabled,
        base_url,
        access_token_not_permitted,
        queue_function_mock,
    ):
        url = f"{base_url}/api/v1/queues/"
        headers = {"Authorization": f"Bearer {access_token_not_permitted}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert queue_function_mock.called is False
