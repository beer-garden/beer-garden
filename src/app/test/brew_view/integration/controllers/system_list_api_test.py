import json
import unittest

from mock import Mock, patch

import brew_view
from bg_utils.mongo.models import Command, Instance, System
from bg_utils.mongo.parser import MongoParser


@unittest.skip("TODO")
class SystemListAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # brew_view.load_app(environment="test")
        cls.parser = MongoParser()

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.default_instance = Instance(name="default", status="RUNNING")
        self.default_command = Command(
            id="54ac18f778c4b57e963f3c18", name="command", description="foo"
        )
        self.default_system = System(
            id="54ac18f778c4b57e963f3c18",
            name="default_system",
            version="1.0.0",
            instances=[self.default_instance],
            commands=[self.default_command],
            max_instances="1",
        )

    @patch("mongoengine.queryset.QuerySet.order_by", Mock(return_value=[]))
    def test_get_emtpy(self):

        response = self.app.get("/api/v1/systems")
        self.assertEqual(200, response.status_code)
        self.assertEqual("[]", response.data)

    @patch("mongoengine.queryset.QuerySet.filter")
    def test_get_ignore_bad_filter_params(self, filter_mock):
        filter_mock.return_value = Mock(order_by=Mock(return_value=[]))
        self.app.get("/api/v1/systems?foo=bar")
        filter_mock.assert_called_with()

    @patch("mongoengine.queryset.QuerySet.filter")
    def test_get_with_filter_params(self, filter_mock):
        filter_mock.return_value = Mock(order_by=Mock(return_value=[]))
        self.app.get("/api/v1/systems?name=bar")
        filter_mock.assert_called_with(name="bar")

    @patch("mongoengine.queryset.QuerySet.order_by")
    def test_get(self, order_mock):
        order_mock.return_value = [self.default_system]

        response = self.app.get("/api/v1/systems")
        self.assertEqual(200, response.status_code)

        response_systems = self.parser.parse_system(
            response.data, many=True, from_string=True
        )
        self.assertEqual(1, len(response_systems))
        self._assert_systems_equal(self.default_system, response_systems[0])

    @patch("mongoengine.queryset.QuerySet.order_by")
    def test_get_no_include_commands(self, order_mock):
        order_mock.return_value = [self.default_system]

        response = self.app.get("/api/v1/systems?include_commands=false")
        self.assertEqual(200, response.status_code)

        response_systems = self.parser.parse_system(
            response.data, many=True, from_string=True
        )
        self.assertEqual(1, len(response_systems))
        self._assert_systems_equal(
            self.default_system, response_systems[0], include_commands=False
        )
        self.assertFalse(response_systems[0].commands)

    @unittest.skip("TODO")
    @patch("bg_utils.parser.BeerGardenParser.parse_system_dict")
    @patch("brew_view.controllers.system_list_api.url_for")
    def test_post_check_calls(self, url_for_mock, parse_mock):
        import flask

        fake_system = Mock(id="id")
        url_for_mock.return_value = "url"
        jsonify_mock = Mock(wraps=flask.jsonify)
        parse_mock.return_value = fake_system

        with patch("brew_view.controllers.system_list_api.jsonify", jsonify_mock):
            rv = self.app.post(
                "/api/v1/systems", data="{}", content_type="application/json"
            )

            parse_mock.assert_called_with({})
            fake_system.deep_save.assert_called_with()
            url_for_mock.assert_called_with("system", _external=True, id="id")
            jsonify_mock.assert_called_with(
                {"message": "Successfully Created System", "system": "url"}
            )
            self.assertEqual(200, rv.status_code)

    @unittest.skip("TODO")
    @patch("bg_utils.parser.BeerGardenParser.parse_system_dict")
    @patch("brew_view.controllers.system_list_api.url_for")
    def test_post_check_response(self, url_for_mock, parse_mock):
        fake_system = Mock(id="id")
        url_for_mock.return_value = "url"
        parse_mock.return_value = fake_system
        rv = self.app.post(
            "/api/v1/systems", data="{}", content_type="application/json"
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEqual(data["message"], "Successfully Created System")
        self.assertEqual(data["system"], "url")

    @unittest.skip("TODO")
    @patch("bg_utils.parser.BeerGardenParser.parse_system_dict")
    def test_post_check_headers(self, parse_mock):
        fake_system = Mock(id="id")
        parse_mock.return_value = fake_system
        rv = self.app.post(
            "/api/v1/systems", data="{}", content_type="application/json"
        )
        self.assertEqual(rv.headers["Location"], "http://localhost/api/v1/systems/id")
        self.assertEqual(200, rv.status_code)
