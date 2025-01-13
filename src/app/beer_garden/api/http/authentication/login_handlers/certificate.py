import logging
from datetime import datetime, timezone
from typing import Optional

from brewtils.models import User
from mongoengine import DoesNotExist
from tornado.httputil import HTTPServerRequest

from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.user import get_user, update_user

logger = logging.getLogger(__name__)


class CertificateLoginHandler(BaseLoginHandler):
    """Handler for client certificate based authentication"""

    def get_user(self, request: HTTPServerRequest) -> Optional[User]:
        """Gets the User corresponding to the ? supplied in the
        request body

        Args:
            request: tornado HTTPServerRequest object

        Returns:
            User: The User object matching the supplied username and password
            None: If no User was found or the supplied password was invalid
        """
        authenticated_user = None
        username = None
        if request:
            cert = request.get_ssl_certificate()
            if cert:
                subject = cert["subject"]
                for sub in subject:
                    for k, v in sub:
                        if k == "commonName":
                            username = v
                            logger.debug(f"Certificate username: {username}")
            else:
                logger.error(f"No certificate was found: {cert}")

            if username:
                try:
                    user = get_user(username=username)

                    authenticated_user = user
                    authenticated_user.metadata["last_authentication"] = datetime.now(
                        timezone.utc
                    ).timestamp()
                    authenticated_user = update_user(user=authenticated_user)

                except DoesNotExist:
                    pass

        return authenticated_user
