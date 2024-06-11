# -*- coding: utf-8 -*-
import json

import pytest
from mongoengine.errors import DoesNotExist
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Role as DB_Role
from beer_garden.db.mongo.models import User as DB_User
from beer_garden.role import create_role
from beer_garden.user import create_user, get_user, verify_password
from brewtils.models import Role, User


@pytest.fixture(autouse=True)
def drop():
    yield
    DB_User.drop_collection()
    DB_Role.drop_collection()


@pytest.fixture
def user_admin_role():
    yield create_role(Role(name="user_admin", permission="GARDEN_ADMIN"))


@pytest.fixture
def user():
    yield create_user(User(username="testuser", password="password", is_remote=False))


@pytest.fixture
def user_admin(user_admin_role):
    yield create_user(
        User(
            username="testuser_admin",
            password="password",
            local_roles=[user_admin_role],
            is_remote=False,
        )
    )


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
            {"operation": "update_roles", "value": {"roles": [user_admin_role.name]}}
        )
        assert len(user.roles) == 0

        response = yield http_client.fetch(
            url, method="PATCH", headers=headers, body=body
        )
        assert response.code == 200

        assert len(get_user(id=user.id).roles) == 1

    @pytest.mark.gen_test
    def test_patch_responds_400_for_no_matching_role(
        self, http_client, base_url, user, user_admin_role
    ):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Content-Type": "application/json"}

        body = json.dumps({"operation": "update", "value": {"roles": ["badrolename"]}})

        assert len(user.roles) == 0

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="PATCH", headers=headers, body=body)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_patch_responds_500_when_no_body_provided(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/users/{user.username}"

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(
                url, method="PATCH", allow_nonstandard_methods=True, body=None
            )

        assert excinfo.value.code == 500

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

        body = json.dumps(
            {"operation": "update_user_password", "value": {"password": "differentpassword"}}
        )

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
        body = json.dumps(
            {"operation": "update", "value": {"password": "differentpassword"}}
        )

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
        with pytest.raises(DoesNotExist):
            get_user(id=user.id)

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
        assert get_user(id=user_admin.id)


class TestUserListAPI:
    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/users/"

        response = yield http_client.fetch(url)
        assert response.code == 200

        response_users = json.loads(response.body.decode("utf-8"))
        assert response_users[0]["id"] == str(user.id)
        assert "password" not in response_users[0].keys()

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


class TestUserPasswordChangeAPI:
    @pytest.mark.gen_test
    def test_post_responds_204_on_success(
        self, http_client, base_url, app_config_auth_enabled, access_token_user, user
    ):
        url = f"{base_url}/api/v1/password/change/"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }

        new_password = "newnewnew"
        body = json.dumps(
            {"current_password": "password", "new_password": new_password}
        )

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=body
        )

        assert response.code == 204

        # Verify password successfully changed
        assert verify_password(get_user(id=user.id), new_password)

    @pytest.mark.gen_test
    def test_post_responds_400_on_incorrect_current_password(
        self, http_client, base_url, app_config_auth_enabled, access_token_user, user
    ):
        url = f"{base_url}/api/v1/password/change/"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }

        body = json.dumps(
            {"current_password": "wrongpassword", "new_password": "newnewnew"}
        )

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", headers=headers, body=body)

        assert excinfo.value.code == 400

        # Verify password remains unchanged
        assert verify_password(get_user(id=user.id), "password")

    @pytest.mark.gen_test
    def test_post_responds_400_when_required_fields_are_missing(
        self, http_client, base_url, app_config_auth_enabled, access_token_user, user
    ):
        url = f"{base_url}/api/v1/password/change/"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", headers=headers, body="{}")

        assert excinfo.value.code == 400

        # Verify password remains unchanged
        assert verify_password(get_user(id=user.id), "password")
