import json
import logging
from datetime import datetime
from typing import List, Optional, cast
from uuid import uuid4

from box import Box
from marshmallow import ValidationError
from mongoengine import DoesNotExist
from tornado.httputil import HTTPHeaders, HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.role import get_role
from beer_garden.user import create_user, get_user, set_password, update_user
from brewtils.models import User
from brewtils.schema_parser import SchemaParser

logger = logging.getLogger(__name__)


class TrustedHeaderLoginHandler(BaseLoginHandler):
    """Handler for certificate based authentication"""

    def __init__(self):
        handler_config = cast(
            Box, config.get("auth.authentication_handlers.trusted_header")
        )
        self.username_header = handler_config.get("username_header")
        self.user_remote_roles_header = handler_config.get("user_remote_roles_header")
        self.user_local_roles_header = handler_config.get("user_local_roles_header")
        self.user_remote_user_mapping_header = handler_config.get(
            "user_remote_user_mapping_header"
        )
        self.create_users = handler_config.get("create_users")

    def get_user(self, request: HTTPServerRequest) -> Optional[User]:
        """Gets the User based on certificates supplied with in the request body

        Args:
            request: tornado HTTPServerRequest object

        Returns:
            User: The User object for the user specified by the certificates
            None: If no User was found
        """
        authenticated_user: Optional[User] = None

        if request.headers:
            username = request.headers.get(self.username_header)
            remote_roles = self._remote_roles_from_headers(request.headers)
            local_roles = self._local_roles_from_headers(request.headers)
            remote_user_mappings = self._remote_user_mapping_from_headers(
                request.headers
            )

            if username:
                try:
                    authenticated_user = get_user(username)
                except DoesNotExist:
                    if self.create_users:
                        authenticated_user = User(username=username, is_remote=True)

                        # TODO: Really we should just have an option on User to disable
                        # password logins. For now, just set a random-ish value.
                        set_password(authenticated_user, str(uuid4()))

                        authenticated_user = create_user(authenticated_user)

                if authenticated_user:
                    if remote_roles:
                        authenticated_user.remote_roles = remote_roles

                    if local_roles:
                        authenticated_user.roles = local_roles

                    if remote_user_mappings:
                        authenticated_user.remote_user_mapping = remote_user_mappings

                    authenticated_user.metadata["last_authentication"] = (
                        datetime.utcnow().timestamp()
                    )
                    authenticated_user = update_user(authenticated_user)

        return authenticated_user

    def _remote_roles_from_headers(self, headers: HTTPHeaders) -> List[str]:
        """Parse the header containing the user's groups and return them as a list"""

        if not headers.get(self.user_remote_roles_header, None):
            return None

        try:
            return SchemaParser.parse_role(
                headers.get(self.user_remote_roles_header, "[]"),
                from_string=True,
                many=True,
            )
        except:
            raise ValidationError(
                f"Unable to parse Remote Roles: {headers.get(self.user_remote_roles_header, '[]')}"
            )

    def _local_roles_from_headers(self, headers: HTTPHeaders) -> List[str]:
        """Parse the header containing the user's groups and return them as a list"""

        if not headers.get(self.user_local_roles_header, None):
            return None

        local_roles = []

        try:
            for role_name in json.loads(
                headers.get(self.user_local_roles_header, "[]")
            ):
                try:
                    get_role(role_name=role_name)
                    local_roles.append(role_name)
                except DoesNotExist:
                    raise ValidationError(
                        f"Invalid role_name {role_name}. No such role found."
                    )
        except:
            raise ValidationError(
                f"Unable to parse Local Roles: {headers.get(self.user_local_roles_header, '[]')}"
            )

        return local_roles

    def _remote_user_mapping_from_headers(self, headers: HTTPHeaders) -> List[str]:
        """Parse the header containing the user's groups and return them as a list"""

        if not headers.get(self.user_remote_user_mapping_header, None):
            return None

        try:
            return SchemaParser.parse_remote_user_map(
                headers.get(self.user_remote_user_mapping_header, "[]"),
                from_string=True,
                many=True,
            )
        except:
            raise ValidationError(
                f"Unable to parse Remote User Mapping: {headers.get(self.user_remote_user_mapping_header, '[]')}"
            )
