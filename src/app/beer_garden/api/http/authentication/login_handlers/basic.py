from datetime import datetime
from typing import Optional

from brewtils.models import User
from tornado.httputil import HTTPServerRequest

from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.api.http.schemas.v1.token import TokenInputSchema
from beer_garden.user import get_user, update_user, verify_password


class BasicLoginHandler(BaseLoginHandler):
    """Handler for username and password based authentication"""

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

                    if verify_password(user, password):
                        authenticated_user = user
                        authenticated_user.metadata["last_authentication"] = (
                            datetime.utcnow().timestamp()
                        )
                        authenticated_user = update_user(user=authenticated_user)

                except User.DoesNotExist:
                    pass

        return authenticated_user
