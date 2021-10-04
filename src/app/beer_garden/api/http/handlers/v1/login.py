# -*- coding: utf-8 -*-
from beer_garden.api.http.authentication import generate_access_token, user_login
from beer_garden.api.http.base_handler import BaseHandler


class LoginAPI(BaseHandler):
    def post(self):
        """
        ---
        summary: User login endpoint
        description: This endpoint is used to do initial authentication via username
                     and password, which grants an access token to be used on
                     for authentication against all other protected endpoints.
        parameters:
          - name: credentials
            in: body
            required: false
            description: The login credentials of the User
            type: string
            schema:
              $ref: '#/definitions/LoginInput'
        responses:
          200:
            description: On successful authentication, a token to be used on subsequent
                         requests. For unsuccessful authentication, a message indicating
                         that login failed.
            schema:
              $ref: '#/definitions/LoginResponse'
        tags:
          - Login
        """
        user = user_login(self.request)

        if user:
            response = {"token": generate_access_token(user), "message": None}
        else:
            response = {
                "token": None,
                "message": "Login with supplied credentials failed",
            }

        self.write(response)
