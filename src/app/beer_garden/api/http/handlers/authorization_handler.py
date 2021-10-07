# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

import jwt

import beer_garden.config as config
from beer_garden.api.authorization import Permissions
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.api.http.exceptions import (
    AuthorizationRequired,
    ExpiredToken,
    InvalidToken,
    RequestForbidden,
)

if TYPE_CHECKING:
    from beer_garden.db.mongo.models import User


class AuthorizationHandler(BaseHandler):
    """Handler that builds on BaseHandler and adds support for authorizing requests
    via a jwt access token supplied in the Authorization header"""

    def get_current_user(self) -> "User":
        """Retrieve the appropriate User object for the request. If the auth setting
        is enabled, the User is determined by the token provided in the Bearer
        Authorization header. If auth is disabled, an anonymous user with full access
        to all gardens is returned"""

        if config.get("auth").enabled:
            return self._get_user_from_request()
        else:
            return self._anonymous_superuser()

    def prepare(self) -> None:
        """Called before each verb handler"""
        # super() must be called first because the BaseHandler's prepare() sets
        # some things that are required in the event that the request ends up going
        # down the error handling path.
        super().prepare()

        # This call forces the authorization check on every request because it calls
        # get_current_user(). The result is cached, so subsequent calls to
        # self.current_user within the life of the request will not result in a
        # duplication of the work required to identify and retrieve the User object.
        _ = self.current_user

    def _anonymous_superuser(self) -> "User":
        """Return a User object with all permissions for all gardens"""

        # Import here to avoid circular import
        from beer_garden.db.mongo.models import Garden, User

        anonymous_superuser = User(username="anonymous")

        # Manually set the permissions cache (to all permissions for all gardens) since
        # the anonymous user has no actual role assignments from which the permissions
        # could be calculated
        permissions = {}
        all_garden_ids = [
            str(garden_id) for garden_id in Garden.objects.all().values_list("id")
        ]

        for permission in Permissions:
            permissions[permission.value] = {"garden_ids": all_garden_ids}

        anonymous_superuser.set_permissions_cache(permissions)

        return anonymous_superuser

    def _get_user_from_request(self) -> "User":
        """Gets the User object corresponding to the jwt access token provided in the
        request.

        Returns:
            User: The User corresponding to the jwt access token in the request

        Raise:
            AuthorizationRequired: If the token is not present or invalid.
            RequestForbidden: If the token is valid, but the corresponding User no
                longer exists.
        """

        # Import here to avoid circular import
        from beer_garden.db.mongo.models import User

        access_token = self._get_token_payload_from_request()

        try:
            user = User.objects.get(id=access_token["sub"])
        except User.DoesNotExist:
            raise RequestForbidden

        user.set_permissions_cache(access_token["permissions"])

        return user

    def _get_token_payload_from_request(self) -> dict:
        """Retrieves and decodes the jwt access token from the Authorization headers
        on the request.

        Raises:
            AuthorizationRequired: The token is not present
        """
        secret_key = config.get("auth").token_secret
        auth_header = self.request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthorizationRequired

        try:
            token = auth_header.split(" ")[1]
            algorithm = jwt.get_unverified_header(token)["alg"]

            return jwt.decode(token, key=secret_key, algorithms=[algorithm])
        except (jwt.InvalidSignatureError, jwt.DecodeError, KeyError, IndexError):
            raise InvalidToken
        except jwt.ExpiredSignatureError:
            raise ExpiredToken
