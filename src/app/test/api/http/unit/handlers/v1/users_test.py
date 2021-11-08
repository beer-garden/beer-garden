# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPError

from beer_garden.db.mongo.models import User


@pytest.fixture
def user():
    user = User(username="testuser")
    user.set_password("password")
    user.save()

    yield user
    user.delete()


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
    def test_patch(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/users/{user.username}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps({"password": "differentpassword"})

        response = yield http_client.fetch(
            url, method="PATCH", headers=headers, body=body
        )

        assert response.code == 200

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
    def test_post(self, http_client, base_url):
        url = f"{base_url}/api/v1/users/"
        headers = {"Content-Type": "application/json"}
        body = json.dumps({"username": "testuser", "password": "password"})

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=body
        )

        assert 201 == response.code

    @pytest.mark.gen_test
    def test_post_responds_400_when_required_fields_are_missing(
        self, http_client, base_url
    ):
        url = f"{base_url}/api/v1/users/"
        headers = {"Content-Type": "application/json"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", headers=headers, body="{}")

        assert excinfo.value.code == 400
