# -*- coding: utf-8 -*-
import json

import pytest
from mock import Mock
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.api.http.handlers.v1.garden
import beer_garden.events
import beer_garden.router
import beer_garden.user
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import (
    Garden,
    Instance,
    Role,
    RoleAssignment,
    System,
    User,
)


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


@pytest.fixture()
def system(garden_permitted):
    instance = Instance(name="instance")
    system = System(
        name="system",
        version="1.0.0",
        namespace=garden_permitted.name,
        instances=[instance],
    ).save()

    yield system
    system.delete()


@pytest.fixture
def garden_admin_role():
    role = Role(
        name="garden_admin",
        permissions=["garden:read", "garden:update", "garden:delete"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def garden_create_role():
    role = Role(
        name="garden_create",
        permissions=["garden:create"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def garden_read_role():
    role = Role(
        name="garden_read",
        permissions=["garden:read"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def garden_none_role():
    role = Role(
        name="garden_none",
        permissions=[],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def garden_cleanup():
    yield
    Garden.drop_collection()


@pytest.fixture
def user(garden_permitted, garden_admin_role, garden_create_role):
    role_assignments = [
        RoleAssignment(
            role=garden_admin_role,
            domain={
                "scope": "Garden",
                "identifiers": {
                    "name": garden_permitted.name,
                },
            },
        ),
        RoleAssignment(
            role=garden_create_role,
            domain={
                "scope": "Global",
            },
        ),
    ]

    user = User(username="testuser", role_assignments=role_assignments).save()

    yield user
    user.delete()


@pytest.fixture
def user_none_role(garden_none_role):
    role_assignments = [
        RoleAssignment(
            role=garden_none_role,
            domain={
                "scope": "Global",
            },
        ),
    ]

    user = User(username="testuser", role_assignments=role_assignments).save()

    yield user
    user.delete()


@pytest.fixture
def read_only_user(garden_permitted, garden_read_role):
    role_assignment = RoleAssignment(
        role=garden_read_role,
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
def global_admin_user(garden_permitted, garden_admin_role):
    role_assignment = RoleAssignment(
        role=garden_admin_role,
        domain={"scope": "Global"},
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def access_token(user):
    yield issue_token_pair(user)["access"]


@pytest.fixture
def none_access_token(user_none_role):
    yield issue_token_pair(user_none_role)["access"]


@pytest.fixture
def read_only_access_token(read_only_user):
    yield issue_token_pair(read_only_user)["access"]


@pytest.fixture
def global_admin_access_token(global_admin_user):
    yield issue_token_pair(global_admin_user)["access"]


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, garden_permitted):
    def mock_determine_target(operation):
        return garden_permitted.name

    def generic_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(beer_garden.events, "publish", generic_mock)
    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "forward", generic_mock)


# class TestGardenAPI:
#    @pytest.mark.gen_test
#    def test_auth_disabled_returns_any_garden(
#        self, http_client, base_url, garden_not_permitted
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"

#        response = yield http_client.fetch(url)
#        response_body = json.loads(response.body.decode("utf-8"))

#        assert response.code == 200
#        assert response_body["id"] == str(garden_not_permitted.id)

#    @pytest.mark.gen_test
#    def test_auth_enabled_returns_permitted_garden(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#        garden_permitted,
#        system,
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_permitted.name}"
#        headers = {"Authorization": f"Bearer {access_token}"}

#        response = yield http_client.fetch(url, headers=headers)
#        response_body = json.loads(response.body.decode("utf-8"))

#        assert response.code == 200
#        assert response_body["id"] == str(garden_permitted.id)
#        assert "connection_params" in response_body.keys()
#        assert len(response_body["systems"]) == 1
#        assert response_body["systems"][0]["name"] == system.name
#        assert len(response_body["namespaces"]) == 1
#        assert response_body["namespaces"][0] == garden_permitted.name

#    @pytest.mark.gen_test
#    def test_auth_enabled_returns_permitted_garden_sans_connection_params(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        read_only_access_token,
#        garden_permitted,
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_permitted.name}"
#        headers = {"Authorization": f"Bearer {read_only_access_token}"}

#        response = yield http_client.fetch(url, headers=headers)
#        response_body = json.loads(response.body.decode("utf-8"))

#        assert response.code == 200
#        assert response_body["id"] == str(garden_permitted.id)
#        assert response_body["connection_params"] == {}

#    # @pytest.mark.gen_test
#    # def test_auth_enabled_returns_403_for_not_permitted_garden(
#    #    self,
#    #    http_client,
#    #    base_url,
#    #    app_config_auth_enabled,
#    #    none_access_token,
#    #    garden_not_permitted,
#    # ):
#    #    url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"
#    #    headers = {"Authorization": f"Bearer {none_access_token}"}
#    #
#    #    with pytest.raises(HTTPError) as excinfo:
#    #        yield http_client.fetch(url, headers=headers)
#    #
#    #    assert excinfo.value.code == 403

#    @pytest.mark.gen_test
#    def test_auth_enabled_allows_patch_for_permitted_garden(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#        garden_permitted,
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_permitted.name}"
#        headers = {
#            "Authorization": f"Bearer {access_token}",
#            "Content-Type": "application/json",
#        }

#        patch_body = [{"operation": "RUNNING"}]
#        request = HTTPRequest(
#            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
#        )
#        response = yield http_client.fetch(request)

#        assert response.code == 200
#        assert Garden.objects.get(id=garden_permitted.id).status == "RUNNING"

#    @pytest.mark.gen_test
#    def test_auth_enabled_rejects_patch_for_not_permitted_garden(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#        garden_not_permitted,
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"
#        headers = {
#            "Authorization": f"Bearer {access_token}",
#            "Content-Type": "application/json",
#        }

#        patch_body = [{"operation": "RUNNING"}]
#        request = HTTPRequest(
#            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
#        )
#        with pytest.raises(HTTPError) as excinfo:
#            yield http_client.fetch(request)

#        assert excinfo.value.code == 403
#        assert (
#            Garden.objects.get(id=garden_not_permitted.id).status
#            == garden_not_permitted.status
#        )

#    @pytest.mark.gen_test
#    def test_auth_disabled_allows_delete(
#        self, base_url, http_client, garden_not_permitted
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"

#        request = HTTPRequest(url, method="DELETE")
#        response = yield http_client.fetch(request)

#        assert response.code == 204
#        assert len(Garden.objects.filter(id=garden_not_permitted.id)) == 0

#    @pytest.mark.gen_test
#    def test_auth_enabled_allows_delete_for_permitted_garden(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#        garden_permitted,
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_permitted.name}"
#        headers = {
#            "Authorization": f"Bearer {access_token}",
#            "Content-Type": "application/json",
#        }

#        request = HTTPRequest(url, method="DELETE", headers=headers)
#        response = yield http_client.fetch(request)

#        assert response.code == 204
#        assert len(Garden.objects.filter(id=garden_permitted.id)) == 0

#    @pytest.mark.gen_test
#    def test_auth_enabled_rejects_delete_for_not_permitted_garden(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#        garden_not_permitted,
#    ):
#        url = f"{base_url}/api/v1/gardens/{garden_not_permitted.name}"
#        headers = {
#            "Authorization": f"Bearer {access_token}",
#            "Content-Type": "application/json",
#        }

#        request = HTTPRequest(url, method="DELETE", headers=headers)

#        with pytest.raises(HTTPError) as excinfo:
#            yield http_client.fetch(request)

#        assert excinfo.value.code == 403
#        assert len(Garden.objects.filter(id=garden_not_permitted.id)) == 1


# class TestGardenListAPI:
#    @pytest.mark.gen_test
#    def test_auth_disabled_returns_all_gardens(self, http_client, base_url):
#        url = f"{base_url}/api/v1/gardens"

#        response = yield http_client.fetch(url)
#        response_body = json.loads(response.body.decode("utf-8"))

#        assert response.code == 200
#        assert len(response_body) == 2

#    @pytest.mark.gen_test
#    def test_auth_enabled_returns_permitted_gardens(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#        garden_permitted,
#        system,
#    ):
#        url = f"{base_url}/api/v1/gardens"
#        headers = {"Authorization": f"Bearer {access_token}"}

#        response = yield http_client.fetch(url, headers=headers)
#        response_body = json.loads(response.body.decode("utf-8"))

#        assert response.code == 200
#        assert len(response_body) == 1
#        assert response_body[0]["id"] == str(garden_permitted.id)
#        assert "connection_params" in response_body[0].keys()
#        assert len(response_body[0]["systems"]) == 1
#        assert response_body[0]["systems"][0]["name"] == system.name
#        assert len(response_body[0]["namespaces"]) == 1
#        assert response_body[0]["namespaces"][0] == garden_permitted.name

#    @pytest.mark.gen_test
#    def test_auth_enabled_returns_permitted_gardens_sans_connection_params(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        read_only_access_token,
#        garden_permitted,
#    ):
#        url = f"{base_url}/api/v1/gardens/"
#        headers = {"Authorization": f"Bearer {read_only_access_token}"}

#        response = yield http_client.fetch(url, headers=headers)
#        response_body = json.loads(response.body.decode("utf-8"))

#        assert response.code == 200
#        assert response_body[0]["connection_params"] == {}

#    @pytest.mark.gen_test
#    def test_auth_enabled_allows_post_with_permission(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#    ):
#        url = f"{base_url}/api/v1/gardens"
#        headers = {"Authorization": f"Bearer {access_token}"}

#        post_body = {
#            "name": "newgarden",
#        }
#        request = HTTPRequest(
#            url, method="POST", headers=headers, body=json.dumps(post_body)
#        )
#        response = yield http_client.fetch(request)

#        assert response.code == 201
#        assert len(Garden.objects.filter(name="newgarden")) == 1

#    @pytest.mark.gen_test
#    def test_auth_enabled_rejects_post_without_permission(
#        self,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        read_only_access_token,
#    ):
#        url = f"{base_url}/api/v1/gardens"
#        headers = {"Authorization": f"Bearer {read_only_access_token}"}
#        garden_count_before = len(Garden.objects.all())

#        post_body = {
#            "name": "newgarden",
#        }

#        request = HTTPRequest(
#            url, method="POST", headers=headers, body=json.dumps(post_body)
#        )

#        with pytest.raises(HTTPError) as excinfo:
#            yield http_client.fetch(request)

#        assert excinfo.value.code == 403
#        assert len(Garden.objects.all()) == garden_count_before

#    @pytest.mark.gen_test
#    def test_auth_enabled_allows_sync_users_patch_with_permissions_to_all_gardens(
#        self,
#        monkeypatch,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        global_admin_access_token,
#    ):
#        monkeypatch.setattr(
#            beer_garden.api.http.handlers.v1.garden, "initiate_user_sync", Mock()
#        )

#        url = f"{base_url}/api/v1/gardens"
#        headers = {
#            "Authorization": f"Bearer {global_admin_access_token}",
#            "Content-Type": "application/json",
#        }

#        patch_body = {
#            "operation": "sync_users",
#        }
#        request = HTTPRequest(
#            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
#        )
#        response = yield http_client.fetch(request)

#        assert response.code == 204
#        assert beer_garden.api.http.handlers.v1.garden.initiate_user_sync.called is True

#    @pytest.mark.gen_test
#    def test_auth_enabled_rejects_sync_users_patch_without_permissions_to_all_gardens(
#        self,
#        monkeypatch,
#        http_client,
#        base_url,
#        app_config_auth_enabled,
#        access_token,
#    ):
#        monkeypatch.setattr(
#            beer_garden.api.http.handlers.v1.garden, "initiate_user_sync", Mock()
#        )

#        url = f"{base_url}/api/v1/gardens"
#        headers = {
#            "Authorization": f"Bearer {access_token}",
#            "Content-Type": "application/json",
#        }

#        patch_body = {
#            "operation": "sync_users",
#        }
#        request = HTTPRequest(
#            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
#        )

#        with pytest.raises(HTTPError) as excinfo:
#            yield http_client.fetch(request)

#        assert excinfo.value.code == 403
#        assert (
#            beer_garden.api.http.handlers.v1.garden.initiate_user_sync.called is False
#        )
