from typing import Optional

from tornado.httputil import HTTPServerRequest

from beer_garden.api.http.authentication.login_handlers.base import BaseLoginHandler
from beer_garden.api.http.schemas.v1.login import LoginInputSchema
from beer_garden.db.mongo.models import User


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
            schema = LoginInputSchema()

            request_data = schema.loads(request.body.decode("utf-8")).data
            username = request_data.get("username")
            password = request_data.get("password")

            if username and password:
                try:
                    user = User.objects.get(username=username)

                    if user.verify_password(password):
                        authenticated_user = user
                except User.DoesNotExist:
                    pass

        return authenticated_user
