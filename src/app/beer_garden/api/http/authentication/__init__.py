from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import jwt
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers import enabled_login_handlers
from beer_garden.authorization import permissions_for_user
from beer_garden.db.mongo.models import User, UserToken
from beer_garden.errors import ExpiredTokenException, InvalidTokenException


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

    for handler in enabled_login_handlers():
        user = handler().get_user(request)

        if user:
            break

    return user


def issue_token_pair(user: User, refresh_expiration: Optional[datetime] = None) -> dict:
    """Issues a JWT access and refresh token pair for a user

    Args:
        user: The User to generate the tokens for

    Returns:
        dict: A dictionary containing an access and refresh token
            { "access": <str>, "refresh": <str> }
    """
    expiration = refresh_expiration or _get_refresh_token_expiration()
    token_uuid = uuid4()

    access_token = _generate_access_token(user, token_uuid)
    refresh_token = _generate_refresh_token(user, token_uuid, expiration)

    UserToken(expires_at=expiration, user=user, uuid=token_uuid).save()

    return {"access": access_token, "refresh": refresh_token}


def refresh_token_pair(refresh_token: str) -> dict:
    """Issues a JWT access and refresh token pair from an existing refresh token.
    Tokens matching the id of the supplied refresh token will be removed from the user's
    list of valid tokens and the newly generated tokens will be added in their place.
    The expiration of the newly issued tokens will match that of the supplied token.

    Args:
        refresh_token: An existing refresh token to be used for determining the user and
            expiration time of the newly issued tokens.

    Returns:
        dict: A dictionary containing an access and refresh token
            { "access": <str>, "refresh": <str> }

    Raises:
        ExpiredTokenException: The supplied refresh token has expired, either due
            to reaching it's natural expiration or having been revoked.
    """
    try:
        decoded_refresh_token = _decode_token(refresh_token)
        refresh_token_obj = UserToken.objects.get(uuid=decoded_refresh_token["jti"])
    except (jwt.ExpiredSignatureError, UserToken.DoesNotExist):
        raise ExpiredTokenException

    expiration = datetime.fromtimestamp(decoded_refresh_token["exp"], tz=timezone.utc)
    user = User.objects.get(id=decoded_refresh_token["sub"])

    new_token_pair = issue_token_pair(user, expiration)
    refresh_token_obj.delete()

    return new_token_pair


def revoke_token_pair(refresh_token: str) -> None:
    """Invalidate the supplied refresh token and its corresponding access token.

    Args:
        refresh_token: The refresh token to be revoked

    Returns:
        None
    """
    try:
        decoded_refresh_token = _decode_token(refresh_token)
        UserToken.objects.get(uuid=decoded_refresh_token["jti"]).delete()
    except (jwt.ExpiredSignatureError, UserToken.DoesNotExist):
        # Since we're trying to revoke the token anyway, do nothing if it was already
        # expired or revoked
        pass


def _generate_access_token(user: User, identifier: UUID) -> str:
    """Generates a JWT access token for a user containing the user's permissions"""
    secret_key = config.get("auth").token_secret

    jwt_headers = {"alg": "HS256", "typ": "JWT"}
    jwt_payload = {
        "jti": str(identifier),
        "sub": str(user.id),
        "iat": datetime.utcnow(),
        "exp": _get_access_token_expiration(),
        "type": "access",
        "username": user.username,
        "permissions": permissions_for_user(user),
    }

    access_token = jwt.encode(jwt_payload, key=secret_key, headers=jwt_headers).decode()

    return access_token


def _generate_refresh_token(user: User, identifier: UUID, expiration: datetime) -> str:
    """Generates a JWT refresh token for a user"""
    secret_key = config.get("auth").token_secret

    jwt_headers = {"alg": "HS256", "typ": "JWT"}
    jwt_payload = {
        "jti": str(identifier),
        "sub": str(user.id),
        "iat": datetime.utcnow(),
        "exp": expiration,
        "type": "refresh",
    }

    refresh_token = jwt.encode(
        jwt_payload, key=secret_key, headers=jwt_headers
    ).decode()

    return refresh_token


def _get_access_token_expiration() -> datetime:
    """Calculate and return the access token expiration time"""
    return datetime.utcnow() + timedelta(minutes=15)


def _get_refresh_token_expiration() -> datetime:
    """Calculate and return the refresh token expiration time"""
    return datetime.utcnow() + timedelta(hours=12)


def _decode_token(token) -> dict:
    """Decode the supplied token and return the contents as a dict"""
    secret_key = config.get("auth").token_secret

    try:
        token_headers = jwt.get_unverified_header(token)
        return jwt.decode(token, key=secret_key, algorithms=[token_headers["alg"]])
    except (jwt.DecodeError, jwt.InvalidSignatureError):
        raise InvalidTokenException
