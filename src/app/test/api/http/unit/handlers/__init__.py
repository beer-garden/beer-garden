from mock import patch
from mongoengine import connect
from tornado.testing import AsyncHTTPTestCase

import beer_garden.api.http


class TestHandlerBase(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        db_patcher = patch("brew_view.setup_database")
        db_patcher.start()
        server_patch = patch("brew_view.HTTPServer")
        server_patch.start()

        beer_garden.api.http.setup([])

        # Setup anonymous user for testing.
        beer_garden.api.http.anonymous_principal = beer_garden.api.http.load_anonymous()

        connect("beer_garden", host="mongomock://localhost")

        cls.app = beer_garden.api.http.tornado_app

    def get_app(self):
        return self.app
