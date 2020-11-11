# -*- coding: utf-8 -*-
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import jwt
from beer_garden.db.mongo.parser import MongoParser
from brewtils.errors import ModelValidationError
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.gen import coroutine
from tornado.web import HTTPError

import beer_garden.api.http
import beer_garden.config as config
from beer_garden.db.mongo.models import Principal, RefreshToken
from beer_garden.api.http.authorization import coalesce_permissions
from beer_garden.api.http.base_handler import BaseHandler


def verify(password, password_hash):
    return custom_app_context.verify(password, password_hash)


class TokenAPI(BaseHandler):
    logger = logging.getLogger(__name__)

    def get(self, token_id):
        """
        ---
        summary: Use a refresh token to retrieve a new access token
        deprecated: true
        description: |
          This endpoint is DEPRECATED - Use GET /api/v1/tokens or PATCH /api/v1/tokens
          instead.
        parameters:
          - name: token_id
            in: path
            required: true
            description: The ID of the Token
            type: string
        responses:
          200:
            description: Refresh Token with the given ID
            schema:
              $ref: '#/definitions/RefreshToken'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        try:
            refresh = RefreshToken.objects.get(id=token_id)

            now = datetime.utcnow()
            if now < refresh.expires:
                self.write(
                    json.dumps({"token": generate_access_token(refresh.payload)})
                )
                return
        except DoesNotExist:
            pass

        raise HTTPError(status_code=403, log_message="Bad credentials")

    def delete(self, token_id):
        """
        ---
        summary: Remove a refresh token
        deprecated: true
        description: |
          This endpoint is DEPRECATED - Use DELETE /api/v1/tokens instead.
        parameters:
          - name: token_id
            in: path
            required: true
            description: The ID of the Token
            type: string
        responses:
          204:
            description: Token has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Deprecated
        """
        RefreshToken.objects.get(id=token_id).delete()

        self.set_status(204)


class TokenListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super(TokenListAPI, self).__init__(*args, **kwargs)

        self.executor = ProcessPoolExecutor()

    def get(self):
        """
        ---
        summary: Use a refresh token to retrieve a new access token
        description: |
          Your refresh token can either be set in a cookie (which we set on your
          session when you logged in) or you can include the refresh ID as a
          header named "X-BG-RefreshID"
        responses:
          200:
            description: New Auth Token
            schema:
              $ref: '#/definitions/RefreshToken'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Tokens
        """
        self.write(json.dumps(self._refresh_token()))

    def patch(self):
        """
        ---
        summary: Refresh an auth token.
        description: |
          The body of the request needs to contain a set of instructions. Currently the
          only operation supported is `refresh`, with path `/payload`:
          ```JSON
          [
            { "operation": "refresh", "path": "/payload", "value": "REFRESH_ID" }
          ]
          ```
          If you do not know your REFRESH_ID, it should be set in a cookie by the
          server. If you leave `value` as `null` and include this cookie, then we
          will automatically refresh. Also, if you are using a cookie, you should
          really consider just using a GET on /api/v1/tokens as it has the same effect.
        parameters:
          - name: patch
            in: body
            required: true
            description: Instructions for what to do
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: New Auth token
            schema:
              $ref: '#/definitions/RefreshToken'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Tokens
        """
        operations = self.parser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )
        token = None

        for op in operations:
            if op.operation == "refresh":
                if op.path == "/payload":
                    token = self._refresh_token(op.value)
                else:
                    raise ModelValidationError("Unsupported path '%s'" % op.path)
            else:
                raise ModelValidationError("Unsupported operation '%s'" % op.operation)

        self.write(json.dumps(token))

    def delete(self):
        """
        ---
        summary: Remove a refresh token
        description: |
          Your refresh token can either be set in a cookie (which we set on your
          session when you logged in) or you can include the refresh ID as a
          header named "X-BG-RefreshID"
        responses:
          204:
            description: Token has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Tokens
        """
        token = self._get_refresh_token()
        if token:
            token.delete()
            self.clear_cookie(self.REFRESH_COOKIE_NAME)
            self.set_status(204)
            return

        raise HTTPError(status_code=403, log_message="Bad credentials")

    @coroutine
    def post(self):
        """
        ---
        summary: Use credentials to generate access and refresh tokens
        responses:
          200:
            description: All Tokens
            schema:
              type: array
              items:
                $ref: '#/definitions/Command'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Tokens
        """
        parsed_body = json.loads(self.request.decoded_body)

        try:
            principal = Principal.objects.get(username=parsed_body["username"])
            if (
                config.get("auth.guest_login_enabled")
                and principal.username
                == beer_garden.api.http.anonymous_principal.username
            ):
                verified = True
            else:
                verified = yield self.executor.submit(
                    verify, str(parsed_body["password"]), str(principal.hash)
                )

            if verified:
                tokens = generate_tokens(principal, self.REFRESH_COOKIE_EXP)

                # This is a semi-done solution. To really do this, we cannot give them
                # a token, instead we should return an error, indicating they need to
                # update their password, and then login again. In the short term, this
                # will be enough. This is really meant only to work for our UI so
                # backwards compatibility is not a concern.
                if principal.metadata.get("auto_change") and not principal.metadata.get(
                    "changed"
                ):
                    self.set_header("change_password_required", "true")

                if parsed_body.get("remember_me", False):
                    self.set_secure_cookie(
                        self.REFRESH_COOKIE_NAME,
                        tokens["refresh"],
                        expires_days=self.REFRESH_COOKIE_EXP,
                    )
                self.write(json.dumps(tokens))
                return
        except DoesNotExist:
            # Still attempt to verify something so the request takes a while
            custom_app_context.verify("", None)

        raise HTTPError(status_code=403, log_message="Bad credentials")

    def _get_refresh_token(self, token_id=None):
        if not token_id:
            token_id = self.get_refresh_id_from_cookie()

        if not token_id and self.request.headers:
            token_id = self.request.headers.get("X-BG-RefreshID", None)

        if token_id:
            try:
                return RefreshToken.objects.get(id=token_id)
            except DoesNotExist:
                pass

        return None

    def _refresh_token(self, token_id=None):
        token = self._get_refresh_token(token_id)
        if token and datetime.utcnow() < token.expires:
            return {"token": generate_access_token(token.payload)}
        else:
            raise HTTPError(status_code=403, log_message="Bad credentials")


def generate_tokens(principal, expire_days):
    roles, permissions = coalesce_permissions(principal.roles)

    payload = {
        "sub": str(principal.id),
        "username": principal.username,
        "roles": list(roles),
        "permissions": list(permissions),
    }

    return {
        "token": generate_access_token(payload),
        "refresh": generate_refresh_token(payload, expire_days),
    }


def generate_access_token(payload, issue_time=None):
    auth_config = config.get("auth")
    issue_time = issue_time or datetime.utcnow()

    access_payload = payload.copy()
    access_payload.update(
        {
            "iat": issue_time,
            "exp": issue_time + timedelta(seconds=auth_config.token.lifetime),
        }
    )

    return jwt.encode(
        access_payload,
        key=auth_config.token.secret,
        algorithm=auth_config.token.algorithm,
    ).decode()


def generate_refresh_token(payload, expire_days, issue_time=None):
    issue_time = issue_time or datetime.utcnow()

    token = RefreshToken(
        issued=issue_time,
        expires=issue_time + timedelta(days=expire_days),
        payload=payload,
    )
    token.save()

    return str(token.id)
