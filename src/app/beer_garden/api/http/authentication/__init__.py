from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import jwt
from brewtils.models import Permissions, User, UserToken
from brewtils.schema_parser import SchemaParser
from mongoengine import DoesNotExist
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers import enabled_login_handlers
from beer_garden.errors import ExpiredTokenException, InvalidTokenException
from beer_garden.user import (
    create_token,
    delete_token,
    determine_max_permission,
    get_token,
    get_user,
    revoke_tokens,
)


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
    max_permission = determine_max_permission(user)
    expiration = refresh_expiration or _get_refresh_token_expiration(max_permission)
    token_uuid = uuid4()

    access_token = _generate_access_token(user, token_uuid, max_permission)
    refresh_token = _generate_refresh_token(user, token_uuid, expiration)

    create_token(
        UserToken(expires_at=expiration, username=user.username, uuid=token_uuid)
    )

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
        ExpiredTokenException: The supplied refresh token has expired, either due to
            reaching it's natural expiration or having been revoked.
        InvalidTokenException: The token could not be decoded or is the incorrect type
            of token and is therefore invalid
    """
    decoded_refresh_token = decode_token(refresh_token)

    try:
        refresh_token_obj = get_token(uuid=decoded_refresh_token["jti"])
    except DoesNotExist:
        raise ExpiredTokenException

    expiration = datetime.fromtimestamp(decoded_refresh_token["exp"], tz=timezone.utc)
    user = get_user(id=decoded_refresh_token["sub"])

    new_token_pair = issue_token_pair(user, expiration)

    delete_token(refresh_token_obj)

    return new_token_pair


def revoke_token_pair(refresh_token: str) -> None:
    """Invalidate the supplied refresh token and its corresponding access token.

    Args:
        refresh_token: The refresh token to be revoked

    Returns:
        None
    """
    try:
        decoded_refresh_token = decode_token(refresh_token)
        delete_token(get_token(uuid=decoded_refresh_token["jti"]))
    except (ExpiredTokenException, DoesNotExist):
        # Since we're trying to revoke the token anyway, do nothing if it was already
        # expired or revoked
        pass


def get_user_from_token(access_token: dict, revoke_expired=True) -> User:
    """Gets the User object corresponding to the jwt access token provided in the
    request.

    Args:
        access_token: A decoded jwt access token
        revoke_expired: Bool determining whether an expired token will result in all
            of a user's tokens being revoked. This should be True when called in a
            context where an expired token could be a sign of a compromised token.

    Returns:
        User: The User corresponding to the jwt access token in the request

    Raise:
        InvalidTokenException: The token is invalid as there is no matching UserToken
        ExpiredTokenException: The token is valid, but the corresponding User no
            longer exists.
    """
    try:
        user = get_user(id=access_token["sub"], include_roles=False)
    except DoesNotExist:
        raise InvalidTokenException

    try:
        _ = get_token(uuid=access_token["jti"])
    except DoesNotExist:
        if revoke_expired:
            revoke_tokens(user=user)

        raise ExpiredTokenException

    user.roles = []
    user.local_roles = SchemaParser.parse_role(
        access_token["roles"], many=True, from_string=False
    )
    user.upstream_roles = []

    return user


def decode_token(encoded_token: str, expected_type: str = None) -> dict:
    """Decodes an encoded access token string

    Args:
        encoded_token: The encoded JWT string
        expected_type: Specify the type of token expecting to be decoded. If specified
            an exception will be thrown if the decoded type does not match. If not
            specified, no check will be performed.

    Returns:
        dict: The decoded access token

    Raises:
        ExpiredTokenException: The token expiration date has passed
        InvalidTokenException: The token could not be decoded or is the incorrect type
            of token and is therefore invalid
    """
    secret_key = config.get("auth").token_secret

    try:
        algorithm = jwt.get_unverified_header(encoded_token)["alg"]
        decoded_token = jwt.decode(
            encoded_token, key=secret_key, algorithms=[algorithm]
        )
    except (jwt.InvalidSignatureError, jwt.DecodeError, KeyError) as exc:
        raise InvalidTokenException(exc)
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenException

    token_type = decoded_token["type"]
    if expected_type and token_type != expected_type:
        raise InvalidTokenException(
            f"Incorrect token type. Expected {expected_type} received {token_type}."
        )

    return decoded_token


def _generate_access_token(user: User, identifier: UUID, max_permission: str) -> str:
    """Generates a JWT access token for a user containing the user's permissions"""
    secret_key = config.get("auth").token_secret

    roles = []

    if user.local_roles:
        for role in user.local_roles:
            roles.append(SchemaParser.serialize_role(role, to_string=False, many=False))

    if user.upstream_roles:
        for role in user.upstream_roles:
            roles.append(
                SchemaParser.serialize_remote_role(role, to_string=False, many=False)
            )

    jwt_headers = {"alg": "HS256", "typ": "JWT"}
    jwt_payload = {
        "jti": str(identifier),
        "sub": str(user.id),
        "iat": datetime.utcnow(),
        "exp": _get_access_token_expiration(max_permission=max_permission),
        "type": "access",
        "username": user.username,
        "roles": roles,
    }

    access_token = jwt.encode(jwt_payload, key=secret_key, headers=jwt_headers)

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

    refresh_token = jwt.encode(jwt_payload, key=secret_key, headers=jwt_headers)

    return refresh_token


def _get_access_token_expiration(max_permission=None) -> datetime:
    """Calculate and return the access token expiration time"""
    if max_permission == Permissions.GARDEN_ADMIN.name:
        return datetime.utcnow() + timedelta(
            minutes=config.get("auth.token_access_ttl.garden_admin")
        )
    elif max_permission == Permissions.PLUGIN_ADMIN.name:
        return datetime.utcnow() + timedelta(
            minutes=config.get("auth.token_access_ttl.plugin_admin")
        )
    elif max_permission == Permissions.OPERATOR.name:
        return datetime.utcnow() + timedelta(
            minutes=config.get("auth.token_access_ttl.operator")
        )
    return datetime.utcnow() + timedelta(
        minutes=config.get("auth.token_access_ttl.read_only")
    )


def _get_refresh_token_expiration(max_permission=None) -> datetime:
    """Calculate and return the refresh token expiration time"""
    if max_permission == Permissions.GARDEN_ADMIN.name:
        return datetime.utcnow() + timedelta(
            minutes=config.get("auth.token_refresh_ttl.garden_admin")
        )
    elif max_permission == Permissions.PLUGIN_ADMIN.name:
        return datetime.utcnow() + timedelta(
            minutes=config.get("auth.token_refresh_ttl.plugin_admin")
        )
    elif max_permission == Permissions.OPERATOR.name:
        return datetime.utcnow() + timedelta(
            minutes=config.get("auth.token_refresh_ttl.operator")
        )
    return datetime.utcnow() + timedelta(
        minutes=config.get("auth.token_refresh_ttl.read_only")
    )
