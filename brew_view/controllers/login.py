from brew_view.base_handler import BaseHandler


class BasicAuthHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            return self._request_auth()
        else:
            self.redirect('/')
