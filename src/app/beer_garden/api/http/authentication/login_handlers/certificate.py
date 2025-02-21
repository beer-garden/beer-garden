import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from brewtils.models import User
from mongoengine import DoesNotExist
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.user import create_user, get_user, set_password, update_user

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
        create_users = config.get(
            "auth.authentication_handlers.certificate.create_users"
        )

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
                    if create_users:
                        authenticated_user = User(username=username)

                        # TODO: Really we should just have an option on User to disable
                        # password logins. For now, just set a random-ish value.
                        set_password(authenticated_user, str(uuid4()))

                        authenticated_user = create_user(authenticated_user)

        return authenticated_user
