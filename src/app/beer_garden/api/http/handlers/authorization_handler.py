# -*- coding: utf-8 -*-
from typing import Type

from brewtils.models import BaseModel as BrewtilsModel
from brewtils.models import Operation, Permissions, Queue, Role, System, User
from mongoengine import Document, QuerySet
from mongoengine.queryset.visitor import Q, QCombination

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.api.http.authentication import decode_token, get_user_from_token
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.api.http.exceptions import (
    AuthorizationRequired,
    NotFound,
    RequestForbidden,
)
from beer_garden.authorization import (
    ModelFilter,
    QueryFilterBuilder,
    check_global_roles,
)

# from beer_garden.db.mongo.models import User
from beer_garden.errors import ExpiredTokenException, InvalidTokenException


class AuthorizationHandler(BaseHandler):
    """Handler that builds on BaseHandler and adds support for authorizing requests
    via a jwt access token supplied in the Authorization header"""

    queryFilter = QueryFilterBuilder()
    modelFilter = ModelFilter()

    minimum_permission = Permissions.READ_ONLY.name

    def get_current_user(self) -> User:
        """Retrieve the appropriate User object for the request. If the auth setting
        is enabled, the User is determined by the token provided in the Bearer
        Authorization header. If auth is disabled, an anonymous user with full access
        to all gardens is returned"""

        if config.get("auth").enabled:
            access_token = self._get_token_payload_from_request()

            try:
                return get_user_from_token(access_token)
            except InvalidTokenException:
                raise RequestForbidden(reason="Authorization token invalid")
            except ExpiredTokenException:
                raise AuthorizationRequired(reason="Authorization token expired")
        else:
            return self._anonymous_superuser()

    async def process_operation(self, operation: Operation, **kwargs):
        return await self.client(
            operation,
            current_user=self.current_user,
            minimum_permission=self.minimum_permission,
            **kwargs,
        )

    def get_or_raise(self, model: Type[BrewtilsModel], **kwargs):  # Updated
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
        if model is Queue:
            if "name" in kwargs:
                system = db.query_unique(
                    System,
                    raise_missing=False,
                    instances__queue_info__request__name=kwargs["name"],
                )
                if not system:
                    system = db.query_unique(
                        System,
                        raise_missing=False,
                        instances__queue_info__admin__name=kwargs["name"],
                    )
                if not system:
                    raise NotFound

                requested_objects = [system]
            else:
                raise NotFound
        else:
            # Change to brewtils query
            provided_filter = Q(**kwargs) & self.queryFilter.build_filter(
                self.current_user, self.minimum_permission, model
            )

            requested_objects = db.query(model, q_filter=provided_filter)
            if len(requested_objects) > 1:
                raise NotFound(
                    "Multiple records returned for schema query: "
                    f"{model.schema}, {provided_filter}"
                )
            elif len(requested_objects) == 0:
                if len(db.query(model, q_filter=Q(**kwargs))) > 0:
                    raise RequestForbidden
                else:
                    raise NotFound

        self.verify_user_permission_for_object(requested_objects[0])

        return requested_objects[0]

    def permissioned_queryset(self, model: Type[Document]) -> QuerySet:  # Updated
        """Returns a QuerySet for the provided Document model filtered down to only
        the objects for which the requesting user has the given permission

        Args:
            model: The Document model to be filtered
            permission: The required permission that will be used to filter objects

        Returns:
            QuerySet: A QuerySet for model filtered down to objects the requesting user
              has access to.
        """

        return self.queryFilter.build_filter(
            self.current_user, self.minimum_permission, model
        )

    def permitted_objects_filter(
        self, model: Type[Document]
    ) -> QCombination:  # Updated
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

        q_filter = self.queryFilter.build_filter(
            self.current_user, self.minimum_permission, model
        )

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

    def verify_user_global_permission(self) -> None:  # Updated
        """Verifies that the requesting use has the specified permission for the Global
        scope.

        Args:
            permission: The permission to check against

        Raises:
            RequestForbidden: The user does not have the required object permissions

        Returns:
            None
        """
        if not check_global_roles(
            self.current_user, permission_level=self.minimum_permission
        ):
            raise RequestForbidden

    def verify_user_permission_for_object(self, obj: BrewtilsModel) -> None:  # Updated
        """Verifies that the requesting user has the specified permission for the
        given object.

        Args:
            permission: The permission to check against
            obj: The object to check against. This can be either a brewtils model

        Raises:
            RequestForbidden: The user does not have the required object permissions

        Returns:
            None
        """

        if not self.modelFilter.filter_object(
            user=self.current_user, permission=self.minimum_permission, obj=obj
        ):
            raise RequestForbidden

    def _anonymous_superuser(self) -> User:  # Updated
        """Return a User object with all permissions for all gardens"""
        anonymous_superuser = User(
            username="anonymous",
            upstream_roles=[],
            local_roles=[
                Role(name="superuser", permission=Permissions.GARDEN_ADMIN.name)
            ],
        )

        # Manually set the permissions cache (to all permissions for all gardens) since
        # the anonymous user has no actual role assignments from which the permissions
        # could be calculated

        return anonymous_superuser

    def _get_token_payload_from_request(self) -> dict:
        """Retrieves and decodes the jwt access token from the Authorization headers
        on the request.

        Raises:
            AuthorizationRequired: The token is not present
            InvalidToken: The supplied token was invalid
        """
        auth_header = self.request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthorizationRequired(reason="No authorization token provided")

        try:
            token = auth_header.split(" ")[1]
            return decode_token(token, expected_type="access")
        except (InvalidTokenException, IndexError):
            raise AuthorizationRequired(reason="Authorization token invalid")
        except ExpiredTokenException:
            raise AuthorizationRequired(reason="Authorization token expired")
