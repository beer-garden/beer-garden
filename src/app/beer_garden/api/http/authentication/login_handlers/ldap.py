from typing import Optional

from ldap3 import SAFE_SYNC, Connection, Server
from ldap3.core.exceptions import LDAPException
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.api.http.schemas.v1.token import TokenInputSchema
from beer_garden.db.mongo.models import User


class LdapLoginHandler(BaseLoginHandler):
    """Handler for username and password ldap based authentication"""

    def get_user_dn(username: str, ou="Users"):
        """This combines user information into a complete user DN"""
        # use cn or uid?
        dn_parts = (f"cn={username}", f"ou={ou}", config.get("ldap.base_dn"))
        return ",".join(dn_parts)

    def verify_ldap_password(self, username: str, password: str):
        """Checks the provided plaintext password against the user's stored password

        Args:
            password: Plaintext string to check against user's password"

        Returns:
            bool: True if the password matches, False otherwise
        """
        try:
            # This depends on how users are organized in the Directory Information Tree (DIT)
            server = Server(host=config.get("ldap.host"), port=config.get("ldap.port"))
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
        server = Server(host=config.get("ldap.host"), port=config.get("ldap.port"))
        with Connection(
            server,
            self.get_user_dn(username),
            password,
            client_strategy=SAFE_SYNC,
            auto_bind=True,
        ) as conn:
            conn.search(
                config.get("ldap.base_dn"),
                f"(&(objectclass=groupOfNames)(member={self.get_user_dn(username)}))",
                attributes=["cn"],
            )
            for entry in conn.entries:
                groups.append(entry["cn"].value)

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
                    user = User.objects.get(username=username)

                    if verify_ldap_password(username, password):
                        authenticated_user = user
                except User.DoesNotExist:
                    pass

        return authenticated_user
