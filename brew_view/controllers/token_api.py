import json
from datetime import datetime, timedelta

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

import brew_view
from bg_utils.models import Principal
from brew_view.authorization import coalesce_permissions
from brew_view.base_handler import BaseHandler


class TokenAPI(BaseHandler):

    def get(self):
        principal = self.get_current_user()

        if principal:
            self.write(json.dumps({
                'token': generate_access_token(principal).decode()
            }))
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
                self.write(json.dumps({
                    'token': generate_access_token(principal).decode()
                }))
                return
        except DoesNotExist:
            # Still attempt to verify something so the request takes a while
            custom_app_context.verify('', None)

        raise HTTPError(status_code=401, log_message='Bad credentials')


def generate_access_token(principal):

    now = datetime.utcnow()
    roles, permissions = coalesce_permissions(principal.roles)

    payload = {
        'sub': str(principal.id),
        'iat': now,
        'exp': now + timedelta(seconds=brew_view.config.auth.token.lifetime),
        'username': principal.username,
        'roles': list(roles),
        'permissions': list(permissions),
    }
    return jwt.encode(payload,
                      key=brew_view.config.auth.token.secret,
                      algorithm=brew_view.config.auth.token.algorithm)
