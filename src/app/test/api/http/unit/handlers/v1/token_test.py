# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import User, UserToken


@pytest.fixture
def user_password():
    yield "supersecret"


@pytest.fixture
def user(user_password):
    user = User(username="testuser")
    user.set_password(user_password)
    user.save()

    yield user
    user.delete()


class TestTokenAPI:
    @pytest.mark.gen_test
    def test_post_returns_token_on_valid_login(
        self, http_client, app_config_auth_enabled, base_url, user, user_password
    ):
        url = f"{base_url}/api/v1/token"
        body = json.dumps({"username": user.username, "password": user_password})

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        access_token = response_body["access"]
        token_headers = jwt.get_unverified_header(access_token)
        decoded_access_token = jwt.decode(
            access_token,
            key=app_config_auth_enabled.auth.token_secret,
            algorithms=[token_headers["alg"]],
        )

        refresh_token = response_body["refresh"]
        token_headers = jwt.get_unverified_header(refresh_token)
        decoded_refresh_token = jwt.decode(
            refresh_token,
            key=app_config_auth_enabled.auth.token_secret,
            algorithms=[token_headers["alg"]],
        )

        assert response.code == 200
        assert decoded_access_token["sub"] == str(user.id)
        assert decoded_access_token["jti"] == decoded_refresh_token["jti"]

    @pytest.mark.gen_test
    def test_post_returns_401_on_invalid_login(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/token"
        body = json.dumps({"username": user.username, "password": "notmypassword"})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 401

    @pytest.mark.gen_test
    def test_post_returns_401_when_user_not_found(self, http_client, base_url):
        url = f"{base_url}/api/v1/token"
        body = json.dumps({"username": "cantfindme", "password": "doesntmatter"})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 401


class TestTokenRefreshAPI:
    @pytest.mark.gen_test
    def test_post_with_valid_refresh_token_returns_new_token_pair(
        self, http_client, base_url, user, app_config_auth_enabled
    ):
        url = f"{base_url}/api/v1/token/refresh"
        expiration = datetime.now(tz=timezone.utc) + timedelta(days=1)
        refresh_token = issue_token_pair(user, expiration)["refresh"]
        body = json.dumps({"refresh": refresh_token})

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        new_access_token = response_body["access"]
        token_headers = jwt.get_unverified_header(new_access_token)
        decoded_access_token = jwt.decode(
            new_access_token,
            key=app_config_auth_enabled.auth.token_secret,
            algorithms=[token_headers["alg"]],
        )

        new_refresh_token = response_body["refresh"]
        token_headers = jwt.get_unverified_header(new_refresh_token)
        decoded_refresh_token = jwt.decode(
            new_refresh_token,
            key=app_config_auth_enabled.auth.token_secret,
            algorithms=[token_headers["alg"]],
        )

        assert response.code == 200
        assert decoded_access_token["sub"] == str(user.id)
        assert decoded_access_token["jti"] == decoded_refresh_token["jti"]

        # Milliseconds get lost during jwt.encode, so we just check the timedelta
        assert (
            expiration
            - datetime.fromtimestamp(decoded_refresh_token["exp"], tz=timezone.utc)
        ) < timedelta(seconds=1)

    @pytest.mark.gen_test
    def test_post_with_expired_refresh_token_returns_400(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/refresh"
        refresh_token = issue_token_pair(user, refresh_expiration=datetime.utcnow())[
            "refresh"
        ]
        body = json.dumps({"refresh": refresh_token})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_post_with_revoked_refresh_token_returns_400(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/refresh"
        refresh_token = issue_token_pair(user, refresh_expiration=datetime.utcnow())[
            "refresh"
        ]
        body = json.dumps({"refresh": refresh_token})

        UserToken.drop_collection()

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_post_with_invalid_refresh_token_returns_400(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/refresh"
        refresh_token = "notarealtoken"
        body = json.dumps({"refresh": refresh_token})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 400


class TestTokenRevokeAPI:
    @pytest.mark.gen_test
    def test_post_with_valid_refresh_token_expires_token(
        self, http_client, base_url, user, app_config_auth_enabled
    ):
        url = f"{base_url}/api/v1/token/revoke"
        refresh_token = issue_token_pair(user)["refresh"]
        body = json.dumps({"refresh": refresh_token})

        token_headers = jwt.get_unverified_header(refresh_token)
        decoded_refresh_token = jwt.decode(
            refresh_token,
            key=app_config_auth_enabled.auth.token_secret,
            algorithms=[token_headers["alg"]],
        )

        assert len(UserToken.objects.filter(uuid=decoded_refresh_token["jti"])) == 1

        response = yield http_client.fetch(url, method="POST", body=body)

        assert response.code == 204
        assert len(UserToken.objects.filter(uuid=decoded_refresh_token["jti"])) == 0

    @pytest.mark.gen_test
    def test_post_with_expired_refresh_token_returns_204(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/revoke"
        refresh_token = issue_token_pair(user, refresh_expiration=datetime.utcnow())[
            "refresh"
        ]
        body = json.dumps({"refresh": refresh_token})

        response = yield http_client.fetch(url, method="POST", body=body)

        assert response.code == 204

    @pytest.mark.gen_test
    def test_post_with_revoked_refresh_token_returns_204(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/revoke"
        refresh_token = issue_token_pair(user)["refresh"]
        body = json.dumps({"refresh": refresh_token})

        UserToken.drop_collection()

        response = yield http_client.fetch(url, method="POST", body=body)

        assert response.code == 204

    @pytest.mark.gen_test
    def test_post_with_invalid_refresh_token_returns_400(
        self, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/revoke"
        refresh_token = "notarealtoken"
        body = json.dumps({"refresh": refresh_token})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 400
