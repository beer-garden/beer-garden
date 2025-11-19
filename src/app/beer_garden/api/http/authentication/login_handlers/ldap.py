import logging
from datetime import datetime, timezone
from typing import Optional

from brewtils.models import User
from ldap3 import Connection, Server
from ldap3.core.exceptions import LDAPException
from mongoengine import DoesNotExist
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.api.http.schemas.v1.token import TokenInputSchema
from beer_garden.role import get_role
from beer_garden.user import create_user, get_user, update_user

logger = logging.getLogger(__name__)


class LdapLoginHandler(BaseLoginHandler):
    """Handler for username and password ldap based authentication"""

    @staticmethod
    def get_user_dn(username: str):
        """This combines user information into a complete user DN"""
        if config.get("auth.authentication_handlers.ldap.use_full_user_dn"):
            return username
        else:
            dn_parts = (
                f"{config.get('auth.authentication_handlers.ldap.user_prefix')}={username}",
                config.get("auth.authentication_handlers.ldap.user_attributes"),
                config.get("auth.authentication_handlers.ldap.base_dn"),
            )
            return ",".join([s for s in dn_parts if s])

    def verify_ldap_password(self, conn: Connection):
        """Checks the provided plaintext password against the user's stored password

        Args:
            password: Plaintext string to check against user's password"

        Returns:
            bool: True if the password matches, False otherwise
        """
        if conn.result["description"] == "success":
            return True
        return False

    def get_user_roles(self, conn: Connection, username: str):
        """Checks the users roles against the provided"""
        groups = set(config.get("auth.authentication_handlers.ldap.default_user_roles"))
        roles = []
        conn.search(
            config.get("auth.authentication_handlers.ldap.roles_search_base"),
            f"(&(objectclass=groupOfNames)(member={self.get_user_dn(username)}))",
            attributes=["cn"],
        )
        for entry in conn.entries:
            groups.add(entry["cn"].value)

        for group in groups:
            try:
                roles.append(get_role(role_name=group))
            except DoesNotExist:
                pass

        logger.info(
            f"Updating {username} local roles to {[role.name for role in roles]}"
        )
        return roles

    def get_connection(self, server, username, password):
        return Connection(
            server,
            self.get_user_dn(username),
            password,
        )

    def get_user(self, request: HTTPServerRequest) -> Optional[User]:
        """Gets the User corresponding to the username and password supplied in the
        request body

        Args:
            request: tornado HTTPServerRequest object

        Returns:
            User: The User object matching the supplied username and password
            None: If no User was found or the supplied password was invalid
        """
        authenticated_user = None

        if request.body:
            schema = TokenInputSchema()

            request_data = schema.loads(request.body.decode("utf-8"))
            username = request_data.get("username")
            password = request_data.get("password")
            host = config.get("auth.authentication_handlers.ldap.host")
            port = config.get("auth.authentication_handlers.ldap.port")

            if username and password:
                try:
                    server = Server(
                        host=host,
                        port=port,
                        use_ssl=config.get("auth.authentication_handlers.ldap.use_ssl"),
                    )
                    with self.get_connection(server, username, password) as conn:
                        if self.verify_ldap_password(conn):
                            try:
                                authenticated_user = get_user(username=username)
                            except DoesNotExist:
                                authenticated_user = User(
                                    username=username, is_remote=True
                                )
                                authenticated_user = create_user(authenticated_user)
                            authenticated_user.metadata["last_authentication"] = (
                                datetime.now(timezone.utc).timestamp()
                            )
                            authenticated_user.local_roles = self.get_user_roles(
                                conn, username
                            )
                            authenticated_user = update_user(user=authenticated_user)
                except LDAPException as ex:
                    logger.error(
                        f"LDAP login failed against {host}:{port} for account "
                        f"{self.get_user_dn(username)}: {ex}"
                    )

        return authenticated_user
