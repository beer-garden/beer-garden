from datetime import datetime, timezone
from typing import Optional

from brewtils.models import User
from ldap3 import SAFE_SYNC, Connection, Server
from ldap3.core.exceptions import LDAPException
from mongoengine import DoesNotExist
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.api.http.schemas.v1.token import TokenInputSchema
from beer_garden.user import get_user, update_user


class LdapLoginHandler(BaseLoginHandler):
    """Handler for username and password ldap based authentication"""

    def __init__(self):
        self.user_prefix = config.get("ldap.user_prefix")
        self.user_attributes = config.get("ldap.user_attributes")
        self.base_dn = config.get("ldap.base_dn")

    @staticmethod
    def get_user_dn(username: str):
        """This combines user information into a complete user DN"""
        dn_parts = (
            f"{config.get('ldap.user_prefix')}={username}",
            config.get("ldap.user_attributes"),
            config.get("ldap.base_dn"),
        )
        return ",".join([s for s in dn_parts if s])

    def verify_ldap_password(self, username: str, password: str):
        """Checks the provided plaintext password against the user's stored password

        Args:
            password: Plaintext string to check against user's password"

        Returns:
            bool: True if the password matches, False otherwise
        """
        try:
            server = Server(
                host=config.get("ldap.host"),
                port=config.get("ldap.port"),
                use_ssl=config.get("ldap.use_ssl"),
            )
            conn = Connection(
                server,
                self.get_user_dn(username),
                password,
                client_strategy=SAFE_SYNC,
                auto_bind=True,
            )
            if conn.result["description"] == "success":
                return True
        except LDAPException:
            raise

        return False

    def get_user_roles(self, username: str, password: str):
        """Checks the users roles against the provided"""
        groups = []
        server = Server(
            host=config.get("ldap.host"),
            port=config.get("ldap.port"),
            use_ssl=config.get("ldap.use_ssl"),
        )
        with Connection(
            server,
            self.get_user_dn(username),
            password,
            client_strategy=SAFE_SYNC,
            auto_bind=True,
        ) as conn:
            conn.search(
                self.base_dn,
                f"(&(objectclass=groupOfNames)(member={self.get_user_dn(username)}))",
                attributes=[self.user_prefix],
            )
            for entry in conn.entries:
                groups.append(entry[self.user_prefix].value)

        return groups

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

            request_data = schema.loads(request.body.decode("utf-8")).data
            username = request_data.get("username")
            password = request_data.get("password")

            if username and password:
                try:
                    user = get_user(username=username)

                    if self.verify_ldap_password(user.username, password):
                        authenticated_user = user
                        authenticated_user.metadata[
                            "last_authentication"
                        ] = datetime.now(timezone.utc).timestamp()
                        authenticated_user = update_user(user=authenticated_user)

                except DoesNotExist:
                    pass

        return authenticated_user
