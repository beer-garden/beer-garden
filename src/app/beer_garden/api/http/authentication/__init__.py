from datetime import datetime, timedelta
from typing import Optional

import jwt
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers import LOGIN_HANDLERS
from beer_garden.authorization import permissions_for_user
from beer_garden.db.mongo.models import User


def user_login(request: HTTPServerRequest) -> Optional[User]:
    """Attempt to authenticate a user based on the information supplied in the request.
    Each handler from beer_garden.api.http.authentication.login_handlers will attempt
    to authenicate the user. Once a successful authentication occurs, no subsequent
    handlers will be tried. If none of the handlers is able to authenticate, the login
    attempt will be denied and None will be returned.

    Args:
        request: The tornado HTTPServerRequest containing login information.

    Returns:
        User: The User object for the successfully authenticated user
        None: If unable to authenticate a user based on the request
    """
    user = None

    for handler in LOGIN_HANDLERS:
        user = handler().get_user(request)

        if user:
            break

    return user


def generate_access_token(user: User) -> str:
    """Generates a JWT access token for a user containing the user's permissions

    Args:
      user: The User to generate the access token for

    Returns:
      str: The encoded JWT
    """
    secret_key = config.get("auth").token_secret

    jwt_headers = {"alg": "HS256", "typ": "JWT"}
    jwt_payload = {
        "sub": str(user.id),
        "exp": _get_token_expiration(),
        "username": user.username,
        "permissions": permissions_for_user(user),
    }

    return jwt.encode(jwt_payload, key=secret_key, headers=jwt_headers).decode()


def _get_token_expiration() -> datetime:
    """Calculate and return the token expiration time"""
    return datetime.utcnow() + timedelta(hours=12)
