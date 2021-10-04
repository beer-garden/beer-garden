from typing import Optional

from tornado.httputil import HTTPServerRequest

from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.db.mongo.models import User


class CertificateLoginHandler(BaseLoginHandler):
    """Handler for certificate based authentication"""

    def get_user(self, request: HTTPServerRequest) -> Optional[User]:
        """Gets the User based on certificates supplied with in the request body

        Args:
            request: tornado HTTPServerRequest object

        Returns:
            User: The User object for the user specified by the certificates
            None: If no User was found
        """
        # This is currently just a stub and will be implemented in a future release
        return None
