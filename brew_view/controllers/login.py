import json

from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from tornado.web import HTTPError

from bg_utils.models import Principal
from brew_view.authorization import generate_token
from brew_view.base_handler import BaseHandler


class LoginHandler(BaseHandler):

    def get(self):
        principal = self.get_current_user()

        if principal:
            self.write(json.dumps({'token': generate_token(principal).decode()}))
        else:
            self._request_basic_auth()

    def post(self):
        parsed_body = json.loads(self.request.decoded_body)

        try:
            principal = Principal.objects.get(username=parsed_body['username'])

            if custom_app_context.verify(parsed_body['password'], principal.hash):
                self.write(json.dumps({'token': generate_token(principal).decode()}))
                return
        except DoesNotExist:
            # Still attempt to verify something so the request takes a while
            custom_app_context.verify('', None)

        raise HTTPError(status_code=401, log_message='Bad credentials')

    def _request_basic_auth(self):
        self.set_header('WWW-Authenticate', 'Basic realm="Beergarden"')
        self.set_status(401)
        self.finish()
