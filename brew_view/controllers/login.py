import json

import jwt

import brew_view
from brew_view.base_handler import BaseHandler


class BasicAuthHandler(BaseHandler):

    def get(self):
        # Get the current user and generate from that
        principal = self.get_current_user()
        if principal:
            pid = str(principal.id)
            payload = {'id': pid, 'username': principal.username}
            token = jwt.encode(payload,
                               brew_view.tornado_app.settings["cookie_secret"],
                               algorithm='HS256')
            self.write(json.dumps({'id': pid, 'token': token.decode()}))
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
