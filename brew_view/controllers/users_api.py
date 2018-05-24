import json

from passlib.apps import custom_app_context

from bg_utils.models import Principal
from brew_view.base_handler import BaseHandler


class UsersHandler(BaseHandler):

    def post(self):
        """Add a new user"""
        parsed = json.loads(self.request.decoded_body)

        hash = custom_app_context.hash(parsed['password'])

        user = Principal(username=parsed['username'], hash=hash)
        user.save()
