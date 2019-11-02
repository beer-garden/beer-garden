# -*- coding: utf-8 -*-
import base64
import datetime

import jwt
from brewtils.models import Principal as BrewtilsPrincipal, Role as BrewtilsRole
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError, RequestHandler

import beer_garden.api.http
from beer_garden.api.auth import coalesce_permissions
from beer_garden.db.mongo.models import Principal, Role


def anonymous_principal():
    """Load correct anonymous permissions

    This exists in a weird space. We need to set the roles attribute to a 'real'
    Role object so it works correctly when the REST handler goes to serialize
    this principal.

    However, we also need to set the permissions attribute to the consolidated
    permission list so that ``check_permission`` will be able to do a comparison
    without having to calculate effective permissions every time.
    """

    auth_config = beer_garden.config.get("auth")
    if auth_config.enabled and auth_config.guest_login_enabled:
        roles = Principal.objects.get(username="anonymous").roles
    elif auth_config.enabled:
        # By default, if no guest login is available, there is no anonymous
        # user, which means there are no roles.
        roles = []
    else:
        roles = [Role(name="bg-admin", permissions=["bg-all"])]

    _, permissions = coalesce_permissions(roles)

    return BrewtilsPrincipal(username="anonymous", roles=roles, permissions=permissions)


def basic_auth(request):
    """Determine if a basic authorization header is valid

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if auth_header is valid, None otherwise
    """
    auth_header = request.headers.get("Authorization")
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


def bearer_auth(request):
    """Determine a principal from a JWT in the Authorization header

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    return _principal_from_token(token)


def query_token_auth(request):
    """Determine a principal from a JWT in query parameter 'token'

    Args:
        request: The request to authenticate

    Returns:
        Brewtils principal if JWT is valid, None otherwise
    """
    token_args = request.query_arguments.get("token", None)
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
    auth_config = beer_garden.config.get("auth")
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
        permissions=decoded.get("permissions", []),
    )


class AuthMixin(RequestHandler):

    auth_providers = [bearer_auth, basic_auth, query_token_auth]

    REFRESH_COOKIE_NAME = "refresh_id"
    REFRESH_COOKIE_EXP = 14

    def get_current_user(self):
        for provider in self.auth_providers:
            user = provider(self.request)

            if user is not None:
                return user

        cookie_user = self.get_user_from_cookie()
        if cookie_user:
            return cookie_user

        return beer_garden.api.http.anonymous_principal

    def get_user_from_cookie(self):
        refresh_id = self.get_secure_cookie(self.REFRESH_COOKIE_NAME)
        if not refresh_id:
            return None

        decoded_refresh = refresh_id.decode()
        token = beer_garden.db.mongo.models.RefreshToken.objects.get(id=decoded_refresh)

        now = datetime.datetime.utcnow()
        if not token or token.expires < now:
            return None

        principal = token.get_principal()
        if not principal:
            return None

        _, principal.permissions = coalesce_permissions(principal.roles)
        token.expires = now + datetime.timedelta(days=self.REFRESH_COOKIE_EXP)
        token.save()

        return principal
