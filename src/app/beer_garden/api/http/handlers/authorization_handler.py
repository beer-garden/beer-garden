# -*- coding: utf-8 -*-
from typing import Type, Union

import jwt
from brewtils.models import BaseModel as BrewtilsModel
from mongoengine import Document, QuerySet, ValidationError
from mongoengine.queryset.visitor import Q, QCombination

import beer_garden.config as config
from beer_garden.api.authorization import Permissions
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.api.http.exceptions import (
    AuthorizationRequired,
    ExpiredToken,
    InvalidToken,
    NotFound,
    RequestForbidden,
)
from beer_garden.authorization import (
    user_has_permission_for_object,
    user_permitted_objects,
    user_permitted_objects_filter,
)
from beer_garden.db.mongo.models import User, UserToken


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

    def get_or_raise(self, model: Type[Document], permission: str, **kwargs):
        """Get Document model objects specified by **kwargs if the requesting user
        has the given permission for that object.

        Args:
            model: The Document based model class of the object to retrieve
            permission: The permission required to access the object
            **kwargs: Used as queryset filter parameters to identify the object

        Returns:
            Document: The requested object, which will be a model class derived from
              Document

        Raises:
            NotFound: The requested object does not exist
            RequestForbidden: This is raised through the permission verification call
              if the requesting user does not have permissions to the object
        """
        provided_filter = Q(**kwargs)

        try:
            requested_object = model.objects.get(provided_filter)
        except (model.DoesNotExist, ValidationError):
            raise NotFound

        self.verify_user_permission_for_object(permission, requested_object)

        return requested_object

    def permissioned_queryset(self, model: Type[Document], permission: str) -> QuerySet:
        """Returns a QuerySet for the provided Document model filtered down to only
        the objects for which the requesting user has the given permission

        Args:
            model: The Document model to be filtered
            permission: The required permission that will be used to filter objects

        Returns:
            QuerySet: A QuerySet for model filtered down to objects the requesting user
              has access to.
        """
        return user_permitted_objects(self.current_user, model, permission)

    def permitted_objects_filter(
        self, model: Type[Document], permission: str
    ) -> QCombination:
        """Returns a QCombination that can be used to filter a QuerySet down to the
        objects for which the requesting user has the given permission.

        Args:
            model: The mongoengine Document class against which access will be checked
            permission: The permission that the user must have in order to be permitted
                access to the object

        Returns:
            QCombination: A mongoengine QCombination filter

        Raises:
            RequestForbidden: The requesting user has access to no objects of the given
                model type
        """
        q_filter = user_permitted_objects_filter(self.current_user, model, permission)

        if q_filter is None:
            raise RequestForbidden

        return q_filter

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

    def verify_user_global_permission(self, permission: str) -> None:
        """Verifies that the requesting use has the specified permission for the Global
        scope.

        Args:
            permission: The permission to check against

        Raises:
            RequestForbidden: The user does not have the required object permissions

        Returns:
            None
        """
        if permission not in self.current_user.global_permissions:
            raise RequestForbidden

    def verify_user_permission_for_object(
        self, permission: str, obj: Union[Document, BrewtilsModel]
    ) -> None:
        """Verifies that the requesting user has the specified permission for the
        given object.

        Args:
            permission: The permission to check against
            obj: The object to check against. This can be either a brewtils model
              or a mongoengine Document model.

        Raises:
            RequestForbidden: The user does not have the required object permissions

        Returns:
            None
        """
        if not user_has_permission_for_object(self.current_user, permission, obj):
            raise RequestForbidden

    def _anonymous_superuser(self) -> "User":
        """Return a User object with all permissions for all gardens"""
        anonymous_superuser = User(username="anonymous")

        # Manually set the permissions cache (to all permissions for all gardens) since
        # the anonymous user has no actual role assignments from which the permissions
        # could be calculated
        permissions = {"global_permissions": [], "domain_permissions": {}}

        for permission in Permissions:
            permissions["global_permissions"].append(permission.value)

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
        access_token = self._get_token_payload_from_request()

        try:
            user = User.objects.get(id=access_token["sub"])
        except User.DoesNotExist:
            raise RequestForbidden

        try:
            _ = UserToken.objects.get(uuid=access_token["jti"])
        except UserToken.DoesNotExist:
            # This could be a sign of a compromised token, so err on the side of caution
            # and remove all of the user's tokens to force them to re-authenticate.
            user.revoke_tokens()
            raise AuthorizationRequired

        user.set_permissions_cache(access_token["permissions"])

        return user

    def _get_token_payload_from_request(self) -> dict:
        """Retrieves and decodes the jwt access token from the Authorization headers
        on the request.

        Raises:
            AuthorizationRequired: The token is not present
            ExpiredToken: The token has expired
            InvalidToken: The token was not valid and failed to decode
        """
        secret_key = config.get("auth").token_secret
        auth_header = self.request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthorizationRequired

        try:
            token = auth_header.split(" ")[1]
            algorithm = jwt.get_unverified_header(token)["alg"]

            decoded_token = jwt.decode(token, key=secret_key, algorithms=[algorithm])
        except (jwt.InvalidSignatureError, jwt.DecodeError, KeyError, IndexError):
            raise InvalidToken
        except jwt.ExpiredSignatureError:
            raise ExpiredToken

        if decoded_token["type"] != "access":
            raise InvalidToken

        return decoded_token
