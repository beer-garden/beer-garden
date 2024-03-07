import logging
from typing import List, Optional, cast
from uuid import uuid4

from box import Box
from brewtils.schema_parser import SchemaParser
from brewtils.models import Role, User
from marshmallow import Schema, ValidationError, fields, post_load, validates
from tornado.httputil import HTTPHeaders, HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.user import create_user, update_user, set_password, get_user

logger = logging.getLogger(__name__)


class TrustedHeaderLoginHandler(BaseLoginHandler):
    """Handler for certificate based authentication"""

    def __init__(self):
        handler_config = cast(
            Box, config.get("auth.authentication_handlers.trusted_header")
        )
        self.username_header = handler_config.get("username_header")
        self.user_roles_header = handler_config.get("user_roles_header")
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

        if request.headers and self.group_mapping:
            username = request.headers.get(self.username_header)
            roles = self._roles_from_headers(request.headers)

            if username:
                try:
                    authenticated_user = get_user(username)
                except User.DoesNotExist:
                    if self.create_users:
                        authenticated_user = User(username=username, is_remote=True)

                        # TODO: Really we should just have an option on User to disable
                        # password logins. For now, just set a random-ish value.
                        set_password(authenticated_user, str(uuid4()))
                        
                        create_user(authenticated_user)

                if authenticated_user:

                    if roles:
                        authenticated_user.remote_roles = roles
                        authenticated_user = update_user(authenticated_user)


        return authenticated_user
    
    def _roles_from_headers(self, headers: HTTPHeaders) -> List[str]:
        """Parse the header containing the user's groups and return them as a list"""

        if not headers.get(self.user_roles_header, None):
            return None

        return SchemaParser.parse_role(headers.get(self.user_roles_header, "[]"), from_string=True, many=True)