import json
from datetime import datetime, timedelta

import jwt

import brew_view
from brew_view.base_handler import BaseHandler


class LoginHandler(BaseHandler):

    def get(self):
        # Get the current user and generate from that
        principal = self.get_current_user()
        if principal:
            current_time = datetime.now()

            payload = {
                'sub': str(principal.id),
                'iat': current_time,
                'exp': current_time + timedelta(minutes=20),
            }
            token = jwt.encode(payload,
                               brew_view.tornado_app.settings["cookie_secret"],
                               algorithm='HS256')
            self.write(json.dumps({'token': token.decode()}))
        else:
            self._request_basic_auth()

    def _request_basic_auth(self):
        self.set_header('WWW-Authenticate', 'Basic realm="Beergarden"')
        self.set_status(401)
        self.finish()


# TODO
class LogoutHandler(BaseHandler):

    def get(self):
        pass
