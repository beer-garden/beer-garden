from brew_view.base_handler import BaseHandler


class BasicAuthHandler(BaseHandler):

    def _request_basic_auth(self):
        self.set_header('WWW-Authenticate', 'Basic realm="Beergarden"')
        self.set_status(401)
        self.finish()

    def get(self):
        # "Logged in" is the presence of a session so if we already have one...
        if self.get_secure_cookie('session'):
            return

        # Otherwise we try to get the current user and generate from that
        principal = self.get_current_user()

        if principal:
            self.set_cookie('user_name', principal.username)
            self.set_cookie('currentTheme', principal.theme)
            self.set_secure_cookie('session', str(principal.id), httponly=True)
        else:
            self._request_basic_auth()


class LogoutHandler(BaseHandler):

    def get(self):
        if not self.get_secure_cookie('session'):
            return

        self.clear_all_cookies()
