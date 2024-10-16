# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from brewtils.models import User, UserToken
from mongoengine import DoesNotExist
from tornado.httpclient import HTTPError

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import UserToken as MongoUserToken
from beer_garden.errors import ExpiredTokenException, InvalidTokenException
from beer_garden.user import create_user, delete_user, get_token


@pytest.fixture
def user_password():
    yield "supersecret"


@pytest.fixture
def user(user_password):
    user = create_user(User(username="testuser", password=user_password))

    yield user
    delete_user(user=user)


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
    def test_post_returns_400_on_invalid_login(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/token"
        body = json.dumps({"username": user.username, "password": "notmypassword"})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_post_returns_400_when_user_not_found(self, http_client, base_url):
        url = f"{base_url}/api/v1/token"
        body = json.dumps({"username": "cantfindme", "password": "doesntmatter"})

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body=body)

        assert excinfo.value.code == 400


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
        self, app_config_auth_enabled, http_client, base_url, user
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
        self, app_config_auth_enabled, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/refresh"
        refresh_token = issue_token_pair(user, refresh_expiration=datetime.utcnow())[
            "refresh"
        ]
        body = json.dumps({"refresh": refresh_token})

        MongoUserToken.drop_collection()

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

        assert get_token(uuid=decoded_refresh_token["jti"])

        response = yield http_client.fetch(url, method="POST", body=body)

        assert response.code == 204
        with pytest.raises(DoesNotExist):
            get_token(uuid=decoded_refresh_token["jti"])

    @pytest.mark.gen_test
    def test_post_with_expired_refresh_token_returns_204(
        self, app_config_auth_enabled, http_client, base_url, user
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
        self, app_config_auth_enabled, http_client, base_url, user
    ):
        url = f"{base_url}/api/v1/token/revoke"
        refresh_token = issue_token_pair(user)["refresh"]
        body = json.dumps({"refresh": refresh_token})

        MongoUserToken.drop_collection()

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
