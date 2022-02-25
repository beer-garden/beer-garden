# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Role, RoleAssignment, User


@pytest.fixture
def user_admin_role():
    role = Role(
        name="user_admin",
        permissions=["user:create", "user:read", "user:update", "user:delete"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user():
    user = User(username="testuser")
    user.set_password("password")
    user.save()

    yield user
    user.delete()


@pytest.fixture
def user_admin(user_admin_role):
    role_assignment = RoleAssignment(role=user_admin_role, domain={"scope": "Global"})
    user = User(username="useradmin")
    user.set_password("password")
    user.role_assignments = [role_assignment]
    user.save()

    yield user
    user.delete()


@pytest.fixture
def access_token_user(user):
    yield issue_token_pair(user)["access"]


@pytest.fixture
def access_token_user_admin(user_admin):
    yield issue_token_pair(user_admin)["access"]


class TestUserAPI:
    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/users/{user.username}"

        response = yield http_client.fetch(url)
        assert response.code == 200

        response_user = json.loads(response.body.decode("utf-8"))
        assert response_user["id"] == str(user.id)
        assert "password" not in response_user.keys()

    @pytest.mark.gen_test
    def test_get_responds_404_when_not_found(self, http_client, base_url):
        url = f"{base_url}/api/v1/users/notauser"

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url)

        assert excinfo.value.code == 404

    @pytest.mark.gen_test
    def test_patch_allows_role_assignment_using_role_name(
        self, http_client, base_url, user, user_admin_role
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(
            {
                "role_assignments": [
                    {
                        "role_name": user_admin_role.name,
                        "domain": {"scope": "Global"},
                    }
                ]
            }
        )
        assert len(user.role_assignments) == 0

        response = yield http_client.fetch(
            url, method="PATCH", headers=headers, body=body
        )
        assert response.code == 200
        assert len(user.reload().role_assignments) == 1

    @pytest.mark.gen_test
    def test_patch_allows_role_assignment_using_role_id(
        self, http_client, base_url, user, user_admin_role
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(
            {
                "role_assignments": [
                    {
                        "role_id": str(user_admin_role.id),
                        "domain": {"scope": "Global"},
                    }
                ]
            }
        )
        assert len(user.role_assignments) == 0

        response = yield http_client.fetch(
            url, method="PATCH", headers=headers, body=body
        )
        assert response.code == 200
        assert len(user.reload().role_assignments) == 1

    @pytest.mark.gen_test
    def test_patch_responds_400_for_no_matching_role(
        self, http_client, base_url, user, user_admin_role
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(
            {
                "role_assignments": [
                    {
                        "role_name": "badrolename",
                        "domain": {"scope": "Global"},
                    }
                ]
            }
        )
        assert len(user.role_assignments) == 0

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="PATCH", headers=headers, body=body)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_patch_responds_400_for_missing_role_identifier(
        self, http_client, base_url, user, user_admin_role
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(
            {
                "role_assignments": [
                    {
                        "domain": {"scope": "Global"},
                    }
                ]
            }
        )
        assert len(user.role_assignments) == 0

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="PATCH", headers=headers, body=body)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_patch_responds_400_when_no_body_provided(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/users/{user.username}"

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(
                url, method="PATCH", allow_nonstandard_methods=True, body=None
            )

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_permitted_user(
        self,
        http_client,
        base_url,
        user,
        app_config_auth_enabled,
        access_token_user_admin,
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {
            "Authorization": f"Bearer {access_token_user_admin}",
            "Content-Type": "application/json",
        }
        body = json.dumps({"password": "differentpassword"})

        response = yield http_client.fetch(
            url, method="PATCH", headers=headers, body=body
        )

        assert response.code == 200

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_not_permitted_user(
        self,
        http_client,
        base_url,
        user_admin,
        app_config_auth_enabled,
        access_token_user,
    ):
        url = f"{base_url}/api/v1/users/{user_admin.username}"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }
        body = json.dumps({"password": "differentpassword"})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="PATCH", headers=headers, body=body)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_auth_enabled_allows_delete_for_permitted_user(
        self,
        http_client,
        base_url,
        user,
        app_config_auth_enabled,
        access_token_user_admin,
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Authorization": f"Bearer {access_token_user_admin}"}

        response = yield http_client.fetch(url, method="DELETE", headers=headers)

        assert response.code == 204
        assert len(User.objects.filter(username=user.username)) == 0

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_delete_for_not_permitted_user(
        self,
        http_client,
        base_url,
        user_admin,
        app_config_auth_enabled,
        access_token_user,
    ):
        url = f"{base_url}/api/v1/users/{user_admin.username}"
        headers = {"Authorization": f"Bearer {access_token_user}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="DELETE", headers=headers)

        assert excinfo.value.code == 403
        assert len(User.objects.filter(username=user_admin.username)) == 1


class TestUserListAPI:
    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/users/"

        response = yield http_client.fetch(url)
        assert response.code == 200

        response_users = json.loads(response.body.decode("utf-8"))
        assert response_users["users"][0]["id"] == str(user.id)
        assert "password" not in response_users["users"][0].keys()

    @pytest.mark.gen_test
    def test_auth_enabled_allows_post_for_permitted_user(
        self, http_client, base_url, app_config_auth_enabled, access_token_user_admin
    ):
        url = f"{base_url}/api/v1/users/"
        headers = {
            "Authorization": f"Bearer {access_token_user_admin}",
            "Content-Type": "application/json",
        }
        body = json.dumps({"username": "newuser", "password": "password"})

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=body
        )

        assert 201 == response.code

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_post_for_not_permitted_user(
        self, http_client, base_url, app_config_auth_enabled, access_token_user
    ):
        url = f"{base_url}/api/v1/users/"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }
        body = json.dumps({"username": "newuser", "password": "password"})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", headers=headers, body=body)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_post_responds_400_when_required_fields_are_missing(
        self, http_client, base_url
    ):
        url = f"{base_url}/api/v1/users/"
        headers = {"Content-Type": "application/json"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", headers=headers, body="{}")

        assert excinfo.value.code == 400
