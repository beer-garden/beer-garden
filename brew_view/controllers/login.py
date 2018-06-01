import json
from datetime import datetime, timedelta

import jwt
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context

import brew_view
from bg_utils.models import Principal
from brew_view.base_handler import BaseHandler


class LoginHandler(BaseHandler):

    def get(self):
        principal = self.get_current_user()

        if principal:
            self.write(json.dumps({'token': self._generate_token(principal).decode()}))
        else:
            self._request_basic_auth()

    def post(self):
        try:
            principal = Principal.objects.get(username=self.get_body_argument('username'))

            if custom_app_context.verify(self.get_body_argument('password'), principal.hash):
                self.write(json.dumps({'token': self._generate_token(principal).decode()}))
        except DoesNotExist:
            pass

    def _generate_token(self, principal):
        current_time = datetime.now()

        payload = {
            'sub': str(principal.id),
            'iat': current_time,
            'exp': current_time + timedelta(minutes=20),
            'roles': [role['name'] for role in principal.roles],
        }
        return jwt.encode(payload,
                          brew_view.tornado_app.settings["cookie_secret"],
                          algorithm='HS256')

    def _request_basic_auth(self):
        self.set_header('WWW-Authenticate', 'Basic realm="Beergarden"')
        self.set_status(401)
        self.finish()


# TODO
class LogoutHandler(BaseHandler):

    def get(self):
        pass
