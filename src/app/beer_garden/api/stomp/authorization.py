# -*- coding: utf-8 -*-
import base64

import jwt

from beer_garden.users import coalesce_permissions
from brewtils.models import (
    Principal as BrewtilsPrincipal,
    Role as BrewtilsRole,
    Permission as BrewtilsPermission,
)
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import beer_garden.api.http
import beer_garden.config as config
from beer_garden.db.mongo.models import Principal
from brewtils.schema_parser import SchemaParser


def anonymous_principal() -> BrewtilsPrincipal:
    """Load correct anonymous permissions

    This exists in a weird space. We need to set the roles attribute to a 'real'
    Role object so it works correctly when the REST handler goes to serialize
    this principal.

    However, we also need to set the permissions attribute to the consolidated
    permission list so that ``check_permission`` will be able to do a comparison
    without having to calculate effective permissions every time.
    """

    # auth_config = config.get("auth")
    # if auth_config.enabled and auth_config.guest_login_enabled:
    #     roles = Principal.objects.get(username="anonymous").roles
    # elif auth_config.enabled:
    #     # By default, if no guest login is available, there is no anonymous
    #     # user, which means there are no roles.
    #     roles = []
    # else:
    #     roles = [
    #         BrewtilsRole(
    #             name="bg-admin",
    #             permissions=[BrewtilsPermission(garden=config.get('garden.name'), access="ADMIN")],
    #         )
    #     ]

    # Once we can properly authenticate users via STOMP, we can add back the true anonymous feature

    roles = [
        BrewtilsRole(
            name="bg-admin",
            permissions=[BrewtilsPermission(garden=config.get('garden.name'), access="ADMIN")],
        )
    ]

    _, permissions = coalesce_permissions(roles)

    return BrewtilsPrincipal(username="anonymous", roles=roles, permissions=permissions)


def basic_auth(headers):
    """Determine if a basic authorization header is valid

    Args:
        headers: The headers to authenticate

    Returns:
        Brewtils principal if auth_header is valid, None otherwise
    """
    auth_header = headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return None

    auth_decoded = base64.b64decode(auth_header[6:]).decode()
    username, password = auth_decoded.split(":")

    try:
        principal = Principal.objects.get(username=username)

        if custom_app_context.verify(password, principal.hash):
            return principal
    except DoesNotExist:
        # Don't handle this differently to prevent an attacker from being able
        #  to enumerate a list of user names
        pass

    return None


def bearer_auth(headers):
    """Determine a principal from a JWT in the Authorization header

    Args:
        headers: The headers to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    auth_header = headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    return _principal_from_token(token)


def query_token_auth(headers):
    """Determine a principal from a JWT in query parameter 'token'

    Args:
        headers: The headers to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    token_args = headers.get("token", None)
    if token_args is None:
        return None

    return _principal_from_token(token_args[0])


def _principal_from_token(token):
    """Determine a principal from a JWT

    Args:
        token: The JWT

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    auth_config = config.get("auth")
    try:
        decoded = jwt.decode(
            token, key=auth_config.token.secret, algorithm=auth_config.token.algorithm
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPError(status_code=401, log_message="Signature expired")

    return BrewtilsPrincipal(
        id=decoded["sub"],
        username=decoded.get("username", ""),
        roles=[BrewtilsRole(name=role) for role in decoded.get("roles", [])],
        permissions=[
            SchemaParser.parse_permission(permission, from_string=True)
            for permission in decoded.get("permissions", [])
        ],
    )


class AuthMixin(object):
    auth_providers: frozenset = None

    def get_current_user(self, headers):
        """Use registered handlers to determine current user"""

        # Until we get the headers setup for proper authentication, we will skip this
        # step for now

        # for provider in self.auth_providers:
        #     principal = provider(headers)
        #
        #     if principal is not None:
        #         return principal

        return beer_garden.api.http.anonymous_principal
