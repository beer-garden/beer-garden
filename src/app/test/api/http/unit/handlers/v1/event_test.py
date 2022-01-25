# -*- coding: utf-8 -*-
import json

import pytest
from brewtils.models import Event, System
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.web import Application
from tornado.websocket import websocket_connect

from beer_garden.api.http.handlers.v1.event import EventSocket


@pytest.fixture
def get_current_user_mock(monkeypatch):
    def get_current_user(self):
        return "someuser"

    monkeypatch.setattr(EventSocket, "get_current_user", get_current_user)


@pytest.fixture
def eventsocket_mock(get_current_user_mock, monkeypatch):
    from beer_garden.api.http.handlers.v1 import event

    def _user_can_receive_messages_for_event(user, event):
        return True

    monkeypatch.setattr(
        event,
        "_user_can_receive_messages_for_event",
        _user_can_receive_messages_for_event,
    )


@pytest.fixture
def user_from_token_mocks(monkeypatch):
    from beer_garden.api.http.handlers.v1 import event

    def decode_token(encoded_token, expected_type):
        return {"access": "mytoken"}

    def get_user_from_token(access_token):
        return "someuser"

    monkeypatch.setattr(event, "decode_token", decode_token)
    monkeypatch.setattr(event, "get_user_from_token", get_user_from_token)


def token_update_message(token):
    return json.dumps({"name": "UPDATE_TOKEN", "payload": token})


class TestEventSocket(AsyncHTTPTestCase):
    path = "/api/v1/socket/events"
    event = Event(name="EVENT", payload_type="System", payload=System(name="mysystem"))

    def get_app(self):
        return Application([(self.path, EventSocket)])

    @gen.coroutine
    def ws_connect(self):
        url = f"ws://localhost:{self.get_http_port()}{self.path}"
        ws = yield websocket_connect(url)
        return ws

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled")
    def test_event_socket_requests_authorization_on_connect(self):
        ws_client = yield self.ws_connect()

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["name"] == "AUTHORIZATION_REQUIRED"

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled", "user_from_token_mocks")
    def test_event_socket_accepts_valid_token_update(self):
        ws_client = yield self.ws_connect()
        yield ws_client.read_message()  # Read the AUTHORIZATION_REQUIRED message

        ws_client.write_message(token_update_message("totallyvalidtoken"))

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["name"] == "TOKEN_UPDATED"

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled")
    def test_event_socket_rejects_invalid_token_update(self):
        ws_client = yield self.ws_connect()
        yield ws_client.read_message()  # Read the AUTHORIZATION_REQUIRED message

        access_token = "invalidtoken"
        ws_client.write_message(token_update_message(access_token))

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["name"] == "AUTHORIZATION_REQUIRED"

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled")
    def test_event_socket_rejects_bad_messages(self):
        ws_client = yield self.ws_connect()
        yield ws_client.read_message()  # Read the AUTHORIZATION_REQUIRED message

        ws_client.write_message("improperly formatted message")

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["name"] == "BAD_MESSAGE"

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_disabled")
    def test_publish_auth_disabled(self):
        ws_client = yield self.ws_connect()
        EventSocket.publish(self.event)

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["payload"]["name"] == self.event.payload.name

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled")
    def test_publish_auth_enabled_requests_authorization(self):
        ws_client = yield self.ws_connect()
        yield ws_client.read_message()  # Read the AUTHORIZATION_REQUIRED message

        EventSocket.publish(self.event)

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["name"] == "AUTHORIZATION_REQUIRED"

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled", "eventsocket_mock")
    def test_publish_auth_enabled_publishes_event_for_authorized_user(self):
        ws_client = yield self.ws_connect()
        yield ws_client.read_message()  # Read the AUTHORIZATION_REQUIRED message

        EventSocket.publish(self.event)

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["payload"]["name"] == self.event.payload.name

    @gen_test
    @pytest.mark.usefixtures("app_config_auth_enabled", "get_current_user_mock")
    def test_publish_auth_enabled_publishes_event_without_payload_type(self):
        ws_client = yield self.ws_connect()
        yield ws_client.read_message()  # Read the AUTHORIZATION_REQUIRED message

        event = Event(name="ENTRY_STARTED")
        EventSocket.publish(event)

        response = yield ws_client.read_message()
        ws_client.close()
        response_dict = json.loads(response)

        assert response_dict["payload"] is None
        assert response_dict["name"] == event.name
