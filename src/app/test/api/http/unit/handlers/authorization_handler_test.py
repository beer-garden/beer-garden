# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta

import pytest
import tornado.web
from box import Box
from mongoengine import connect
from tornado.httpclient import HTTPError

import beer_garden.api.http.authentication
from beer_garden import config
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.api.http.handlers.v1.user import WhoAmIAPI
from beer_garden.db.mongo.models import User

# TODO: Load this from conftest using the actual _setup_application call
application = tornado.web.Application(
    [
        (r"/api/v1/whoami/?", WhoAmIAPI),
    ]
)


@pytest.fixture
def app_config_auth_enabled(monkeypatch):
    app_config = Box({"auth": {"enabled": True, "token_secret": "notsosecret"}})
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


@pytest.fixture
def app_config_auth_disabled(monkeypatch):
    app_config = Box({"auth": {"enabled": False, "token_secret": "notsosecret"}})
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


@pytest.fixture
def user_password():
    yield "supersecret"


@pytest.fixture
def user(user_password):
    user = User(username="testuser").save()

    yield user
    user.delete()


@pytest.fixture
def access_token(user):
    yield issue_token_pair(user)["access"]


@pytest.fixture
def app():
    return application


class TestAuthorizationHandler:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_auth_disabled_allows_anonymous_access(
        self, http_client, app_config_auth_disabled, base_url
    ):
        url = f"{base_url}/api/v1/whoami"

        response = yield http_client.fetch(url)

        assert response.code == 200

    @pytest.mark.gen_test
    def test_auth_enabled_blocks_anonymous_access(
        self, http_client, app_config_auth_enabled, base_url
    ):
        url = f"{base_url}/api/v1/whoami"

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url)

        assert excinfo.value.code == 401

    @pytest.mark.gen_test
    def test_auth_enabled_allows_access_with_valid_token(
        self, http_client, base_url, app_config_auth_enabled, user, access_token
    ):
        url = f"{base_url}/api/v1/whoami"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)

        assert response.code == 200

    @pytest.mark.gen_test
    def test_auth_enabled_blocks_access_with_invalid_token_signature(
        self, http_client, base_url, app_config_auth_enabled, user, access_token
    ):
        url = f"{base_url}/api/v1/whoami"

        token_header, token_payload, token_signature = access_token.split(".")
        access_token_bad_signature = f"{token_header}.{token_payload}.badsignature"

        headers = {"Authorization": f"Bearer {access_token_bad_signature}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        response_body = json.loads(excinfo.value.response.body.decode("utf-8"))

        assert excinfo.value.code == 401
        assert "invalid" in response_body["message"]

    @pytest.mark.gen_test
    def test_auth_enabled_blocks_access_with_invalid_token_header(
        self, http_client, base_url, app_config_auth_enabled, user, access_token
    ):
        url = f"{base_url}/api/v1/whoami"

        token_header, token_payload, token_signature = access_token.split(".")
        access_token_bad_header = f"badheader.{token_payload}.{token_signature}"

        headers = {"Authorization": f"Bearer {access_token_bad_header}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        response_body = json.loads(excinfo.value.response.body.decode("utf-8"))

        assert excinfo.value.code == 401
        assert "invalid" in response_body["message"]

    @pytest.mark.gen_test
    def test_auth_enabled_blocks_access_with_invalid_token_payload(
        self, http_client, base_url, app_config_auth_enabled, user, access_token
    ):
        url = f"{base_url}/api/v1/whoami"

        token_header, token_payload, token_signature = access_token.split(".")
        access_token_bad_payload = f"{token_header}.badpayload.{token_signature}"

        headers = {"Authorization": f"Bearer {access_token_bad_payload}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        response_body = json.loads(excinfo.value.response.body.decode("utf-8"))

        assert excinfo.value.code == 401
        assert "invalid" in response_body["message"]

    @pytest.mark.gen_test
    def test_auth_enabled_blocks_access_with_expired_token(
        self, monkeypatch, http_client, base_url, app_config_auth_enabled, user
    ):
        def yesterday():
            return datetime.utcnow() - timedelta(days=1)

        monkeypatch.setattr(
            beer_garden.api.http.authentication,
            "_get_access_token_expiration",
            yesterday,
        )

        url = f"{base_url}/api/v1/whoami"

        access_token = issue_token_pair(user)["access"]
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        response_body = json.loads(excinfo.value.response.body.decode("utf-8"))

        assert excinfo.value.code == 401
        assert "expired" in response_body["message"]

    @pytest.mark.gen_test
    def test_auth_enabled_blocks_access_with_refresh_token(
        self, http_client, base_url, app_config_auth_enabled, user
    ):

        url = f"{base_url}/api/v1/whoami"

        refresh_token = issue_token_pair(user)["refresh"]
        headers = {"Authorization": f"Bearer {refresh_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        response_body = json.loads(excinfo.value.response.body.decode("utf-8"))

        assert excinfo.value.code == 401
        assert "invalid" in response_body["message"]
