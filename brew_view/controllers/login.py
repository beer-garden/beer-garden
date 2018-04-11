import logging

from tornado.gen import coroutine

import brew_view
from brew_view import thrift_context
from brew_view.base_handler import BaseHandler


class BasicAuthHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            return self._request_auth()
        else:
            self.redirect('/')
