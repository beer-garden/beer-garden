import json
import unittest

from mock import Mock, patch

from beer_garden.db.mongo.models import Garden
from beer_garden.db.mongo.parser import MongoParser


@unittest.skip("TODO")
class GardenListAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # brew_view.load_app(environment="test")
        cls.parser = MongoParser()

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.default_garden = Garden(
            garden_name="default",
            status="RUNNING",
            connection_type="http",
            connection_params={"host": "local"},
        )

    @patch("mongoengine.queryset.QuerySet.order_by", Mock(return_value=[]))
    def test_get_emtpy(self):
        response = self.app.get("/api/v1/garden")
        self.assertEqual(200, response.status_code)
        self.assertEqual("[]", response.data)

    @patch("mongoengine.queryset.QuerySet.order_by")
    def test_get(self, order_mock):
        order_mock.return_value = [self.default_system]

        response = self.app.get("/api/v1/garden")
        self.assertEqual(200, response.status_code)

        response_systems = self.parser.parse_system(
            response.data, many=True, from_string=True
        )
        self.assertEqual(1, len(response_systems))
        self._assert_systems_equal(self.default_system, response_systems[0])
