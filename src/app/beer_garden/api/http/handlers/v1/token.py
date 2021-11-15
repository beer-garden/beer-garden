# -*- coding: utf-8 -*-
from beer_garden.api.http.authentication import (
    issue_token_pair,
    refresh_token_pair,
    revoke_token_pair,
    user_login,
)
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.api.http.exceptions import AuthenticationFailed, BadRequest
from beer_garden.api.http.schemas.v1.token import TokenRefreshInputSchema
from beer_garden.errors import ExpiredTokenException, InvalidTokenException


class TokenAPI(BaseHandler):
    def post(self):
        """
        ---
        summary: User login endpoint
        description: This endpoint is used to do initial authentication via username
                     and password, which grants an access token to be used on
                     for authentication against all other protected endpoints, as well
                     as a refresh token for renewing the access token.
        parameters:
          - name: credentials
            in: body
            required: false
            description: The login credentials of the User
            type: string
            schema:
              $ref: '#/definitions/TokenInput'
        responses:
          200:
            description: On successful authentication, a token to be used on subsequent
                         requests as well as a refresh token for renewing the access
                         token.
            schema:
              $ref: '#/definitions/TokenResponse'
          401:
            description: Authentication failed.
        tags:
          - Token
        """
        user = user_login(self.request)

        if user:
            response = issue_token_pair(user)
        else:
            raise AuthenticationFailed

        self.write(response)


class TokenRefreshAPI(BaseHandler):
    def post(self):
        """
        ---
        summary: Token refresh endpoint
        description: This endpoint is used to do retrieve a new access token and refresh
                     token pair using an existing refresh token.
        parameters:
          - name: refresh
            in: body
            required: true
            description: A valid refresh token, previously retrieved via either the
                         /token /token/refresh endpoints.
            type: string
            schema:
              $ref: '#/definitions/TokenRefreshInput'
        responses:
          200:
            description: An access and refresh token pair. The issued pair will replace
                         the pair with the supplied refresh token's identifier in the
                         user's list of valid tokens. The expiration time of the new
                         refresh token will be the same as that of the supplied token.
            schema:
              $ref: '#/definitions/TokenResponse'
          400:
            description: The provided refresh token is invalid, possibly because it has
              expired or been revoked.
        tags:
          - Token
        """
        refresh_token = self.schema_validated_body(TokenRefreshInputSchema)["refresh"]

        try:
            response = refresh_token_pair(refresh_token=refresh_token)
        except (ExpiredTokenException, InvalidTokenException):
            raise BadRequest(reason="Invalid or expired token")

        self.write(response)


class TokenRevokeAPI(BaseHandler):
    def post(self):
        """
        ---
        summary: Revoke a token pair
        description: This endpoint is used to revoke an issued refresh token and any
          access tokens issued along with it. For added safety, this should be called
          when a user intends to log out and end their session.
        parameters:
          - name: refresh
            in: body
            required: true
            description: The refresh token to revoke
            type: string
            schema:
              $ref: '#/definitions/TokenRefreshInput'
        responses:
          204:
            description: Token successfully revoked
          400:
            description: The provided refresh token is invalid
        tags:
          - Token
        """
        refresh_token = self.schema_validated_body(TokenRefreshInputSchema)["refresh"]

        try:
            revoke_token_pair(refresh_token)
        except InvalidTokenException:
            raise BadRequest(reason="Invalid token")

        self.set_status(204)
