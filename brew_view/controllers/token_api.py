import json
from datetime import datetime, timedelta

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import brew_view
from bg_utils.models import Principal, RefreshToken
from brew_view.authorization import coalesce_permissions
from brew_view.base_handler import BaseHandler


class TokenAPI(BaseHandler):

    def get(self):
        principal = self.get_current_user()

        if principal:
            self.write(json.dumps(generate_tokens(principal)))
        else:
            # Request Basic Auth
            self.set_header('WWW-Authenticate', 'Basic realm="Beergarden"')
            self.set_status(401)
            self.finish()

    def post(self):
        parsed_body = json.loads(self.request.decoded_body)

        try:
            principal = Principal.objects.get(username=parsed_body['username'])

            if custom_app_context.verify(parsed_body['password'], principal.hash):
                self.write(json.dumps(generate_tokens(principal)))
                return
        except DoesNotExist:
            # Still attempt to verify something so the request takes a while
            custom_app_context.verify('', None)

        raise HTTPError(status_code=401, log_message='Bad credentials')


class RefreshAPI(BaseHandler):

    def get(self):

        refresh_token = self.get_query_argument('refresh_token')

        try:
            refresh = RefreshToken.objects.get(id=refresh_token)
        except Exception as ex:
            raise HTTPError(status_code=401, log_message='Bad credentials')

        now = datetime.utcnow()
        if now < refresh.expires:
            self.write(json.dumps({
                'token': generate_access_token(refresh.payload)
            }))
        else:
            raise HTTPError(status_code=401, log_message='Bad credentials')


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
        issued_at=issue_time,
        expires=issue_time + timedelta(hours=24),
        payload=payload,
    )
    token.save()

    return str(token.id)
