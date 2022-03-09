# -*- coding: utf-8 -*-
import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Optional

from brewtils.models import Events
from brewtils.schema_parser import SchemaParser
from marshmallow import Schema, ValidationError, fields, validate
from tornado.websocket import WebSocketHandler

from beer_garden import config
from beer_garden.api.authorization import Permissions
from beer_garden.api.http.authentication import decode_token, get_user_from_token
from beer_garden.authorization import user_has_permission_for_object
from beer_garden.errors import ExpiredTokenException, InvalidTokenException

if TYPE_CHECKING:
    from brewtils.models import Event

    from beer_garden.db.mongo.models import User


logger = logging.getLogger(__name__)

# Event types that should never be published to the websocket
WEBSOCKET_EVENT_TYPE_BLOCKLIST = [Events.USER_UPDATED.name]


def _auth_enabled():
    """Helper for checking the auth.enabled settings"""
    return config.get("auth").enabled


def _user_can_receive_messages_for_event(user: "User", event: "Event"):
    """Check a that a user has access to view the supplied event"""
    user_permitted = True

    # Event types that won't have a payload, but still require a permission check
    # TODO: Really every event type ought to be included here
    event_permission_map = {Events.USERS_IMPORTED.name: Permissions.GARDEN_UPDATE.value}

    if event.payload and event.payload_type:
        user_permitted = user_has_permission_for_object(
            user, f"{event.payload_type.lower()}:read", event.payload
        )
    elif event.name in event_permission_map:
        user_permitted = event_permission_map[event.name] in user.global_permissions

    return user_permitted


class IncomingMessageSchema(Schema):
    """A simple schema for validating incoming messages. Currently only handles access
    token updates."""

    name = fields.Str(required=True, validate=validate.OneOf(["UPDATE_TOKEN"]))
    payload = fields.Str(required=True)


class EventSocket(WebSocketHandler):

    closing = False
    listeners = set()

    def __init__(self, *args, **kwargs):
        self.access_token: Optional[dict] = None

        super().__init__(*args, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        if EventSocket.closing:
            self.close(reason="Shutting down")
            return

        EventSocket.listeners.add(self)

        if _auth_enabled():
            self.request_authorization(reason="Access token required")

    def on_close(self):
        EventSocket.listeners.discard(self)

    def on_message(self, message):
        """Process incoming messages. Called by WebSocketHandler automatically when
        a message is received."""
        try:
            token = IncomingMessageSchema(strict=True).loads(message).data["payload"]
            self._update_access_token(token)
        except (ValidationError, JSONDecodeError) as exc:
            self._message_processing_error(
                f"Invalid message received. Error was: {exc}"
            )

    def get_current_user(self) -> Optional["User"]:
        """Retrieve the appropriate User object for the websocket connection.

        Returns:
            None: The token for the current connection is invalid or expired
            User: The User associated with the connection token
        """
        user = None

        if _auth_enabled() and self.access_token is not None:
            try:
                user = get_user_from_token(self.access_token, revoke_expired=False)
            except (ExpiredTokenException, InvalidTokenException):
                pass

        return user

    def request_authorization(self, reason: str):
        """Publish a message requesting authorization"""
        message = {"name": "AUTHORIZATION_REQUIRED", "payload": reason}
        self.write_message(message)

    def _message_processing_error(self, reason: str):
        """Publish a message reporting an error while handling incoming messages"""
        message = {"name": "BAD_MESSAGE", "payload": reason}
        self.write_message(message)

    def _update_access_token(self, token):
        """Update the access token for the connection"""
        try:
            decoded_token = decode_token(token, expected_type="access")
            _ = get_user_from_token(decoded_token)

            self.access_token = decoded_token
            self.write_message({"name": "TOKEN_UPDATED"})
        except (ExpiredTokenException, InvalidTokenException):
            self.access_token = None
            self.request_authorization(
                "Access token update message contained an invalid token"
            )

    @classmethod
    def publish(cls, event):
        if event.name in WEBSOCKET_EVENT_TYPE_BLOCKLIST:
            return

        if len(cls.listeners) > 0:
            message = SchemaParser.serialize(event, to_string=True)

            for listener in cls.listeners:
                if _auth_enabled():
                    user = listener.get_current_user()

                    if user is None:
                        listener.request_authorization("Valid access token required")
                        continue

                    if not _user_can_receive_messages_for_event(user, event):
                        logger.debug(
                            "Skipping websocket publish of event %s to user %s due to "
                            "lack of access",
                            event.name,
                            user.username,
                        )
                        continue

                listener.write_message(message)

    @classmethod
    def shutdown(cls):
        logger.debug("Closing websocket connections")
        EventSocket.closing = True

        for listener in cls.listeners:
            listener.close(reason="Shutting down")
