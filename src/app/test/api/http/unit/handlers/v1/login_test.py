# -*- coding: utf-8 -*-
import json

import jwt
import pytest
import tornado.web
from box import Box
from mongoengine import connect

from beer_garden import config
from beer_garden.api.http.handlers.v1.login import LoginAPI
from beer_garden.db.mongo.models import User

# TODO: Load this from conftest using the actual _setup_application call
application = tornado.web.Application(
    [
        (r"/api/v1/login/?", LoginAPI),
    ]
)


@pytest.fixture(autouse=True)
def app_config(monkeypatch):
    app_config = Box({"auth": {"enabled": False, "token_secret": "keepitsecret"}})
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


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


@pytest.fixture
def app():
    return application


class TestLoginAPI:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_post_returns_token_on_valid_login(
        self, http_client, app_config, base_url, user, user_password
    ):
        url = f"{base_url}/api/v1/login"
        body = json.dumps({"username": user.username, "password": user_password})

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        token = response_body["token"]
        token_headers = jwt.get_unverified_header(token)
        decoded_token = jwt.decode(
            token, key=app_config.auth.token_secret, algorithms=[token_headers["alg"]]
        )

        assert response.code == 200
        assert decoded_token["sub"] == str(user.id)

    @pytest.mark.gen_test
    def test_post_returns_message_on_invalid_login(self, http_client, base_url, user):
        url = f"{base_url}/api/v1/login"
        body = json.dumps({"username": user.username, "password": "notmypassword"})

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["token"] is None
        assert response_body["message"] is not None

    @pytest.mark.gen_test
    def test_post_returns_message_when_user_not_found(self, http_client, base_url):
        url = f"{base_url}/api/v1/login"
        body = json.dumps({"username": "cantfindme", "password": "doesntmatter"})

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["token"] is None
        assert response_body["message"] is not None
