from mock import patch
from mongoengine import connect
from tornado.testing import AsyncHTTPTestCase
from yapconf import YapconfSpec

import brew_view
from brew_view.specification import SPECIFICATION


class TestHandlerBase(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        db_patcher = patch("brew_view.setup_database")
        db_patcher.start()
        server_patch = patch("brew_view.HTTPServer")
        server_patch.start()

        spec = YapconfSpec(SPECIFICATION)
        brew_view.setup(spec, {})
        connect("beer_garden", host="mongomock://localhost")

        cls.app = brew_view.tornado_app

    def get_app(self):
        return self.app
