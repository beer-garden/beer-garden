import json
import logging
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.gen import coroutine
from tornado.web import HTTPError

import brew_view
from bg_utils.models import Principal, RefreshToken
from brew_view.authorization import coalesce_permissions
from brew_view.base_handler import BaseHandler


def verify(password, password_hash):
    return custom_app_context.verify(password, password_hash)


class TokenAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    def get(self, token_id):
        """
        ---
        summary: Use a refresh token to retrieve a new access token
        parameters:
          - name: token_id
            in: path
            required: true
            description: The ID of the Token
            type: string
        responses:
          200:
            description: System with the given ID
            schema:
              $ref: '#/definitions/System'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Tokens
        """
        try:
            refresh = RefreshToken.objects.get(id=token_id)

            now = datetime.utcnow()
            if now < refresh.expires:
                self.write(json.dumps({
                    'token': generate_access_token(refresh.payload)
                }))
                return
        except DoesNotExist:
            pass

        raise HTTPError(status_code=403, log_message='Bad credentials')

    def delete(self, token_id):
        """
        ---
        summary: Remove a refresh token
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
          - Tokens
        """
        RefreshToken.objects.get(id=token_id).delete()

        self.set_status(204)


class TokenListAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super(TokenListAPI, self).__init__(*args, **kwargs)

        self.executor = ProcessPoolExecutor()

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
            principal = Principal.objects.get(username=parsed_body['username'])

            verified = yield self.executor.submit(
                verify, str(parsed_body['password']), str(principal.hash))

            if verified:
                self.write(json.dumps(generate_tokens(principal)))
                return
        except DoesNotExist:
            # Still attempt to verify something so the request takes a while
            custom_app_context.verify('', None)

        raise HTTPError(status_code=403, log_message='Bad credentials')


def generate_tokens(principal):

    roles, permissions = coalesce_permissions(principal.roles)

    payload = {
        'sub': str(principal.id),
        'username': principal.username,
        'roles': list(roles),
        'permissions': list(permissions),
    }

    return {
        'token': generate_access_token(payload),
        'refresh': generate_refresh_token(payload),
    }


def generate_access_token(payload, issue_time=None):
    issue_time = issue_time or datetime.utcnow()

    access_payload = payload.copy()
    access_payload.update({
        'iat': issue_time,
        'exp': issue_time + timedelta(seconds=brew_view.config.auth.token.lifetime),
    })

    return jwt.encode(access_payload,
                      key=brew_view.config.auth.token.secret,
                      algorithm=brew_view.config.auth.token.algorithm).decode()


def generate_refresh_token(payload, issue_time=None):

    issue_time = issue_time or datetime.utcnow()

    token = RefreshToken(
        issued=issue_time,
        expires=issue_time + timedelta(hours=24),
        payload=payload,
    )
    token.save()

    return str(token.id)
