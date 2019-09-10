from mock import patch
from mongoengine import connect
from tornado.testing import AsyncHTTPTestCase
from yapconf import YapconfSpec

import beer_garden.brew_view
from beer_garden.brew_view.specification import SPECIFICATION


class TestHandlerBase(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        db_patcher = patch("brew_view.setup_database")
        db_patcher.start()
        server_patch = patch("brew_view.HTTPServer")
        server_patch.start()

        spec = YapconfSpec(SPECIFICATION)
        beer_garden.brew_view.setup(spec, {})

        # Setup anonymous user for testing.
        beer_garden.brew_view.anonymous_principal = (
            beer_garden.brew_view.load_anonymous()
        )

        connect("beer_garden", host="mongomock://localhost")

        cls.app = beer_garden.brew_view.tornado_app

    def get_app(self):
        return self.app
