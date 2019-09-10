import json
import unittest

from mock import MagicMock, Mock, patch

import beer_garden.brew_view
from beer_garden.__version__ import __version__


@unittest.skip("TODO")
class UIControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass
        # brew_view.load_app(environment="test")

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.client_mock = Mock(name="client_mock")
        self.fake_context = MagicMock(
            __enter__=Mock(return_value=self.client_mock),
            __exit__=Mock(return_value=False),
        )

    @patch("__builtin__.open")
    def test_read_index_file(self, open_mock):
        open_mock.return_value = Mock(read=Mock(return_value="index_contents"))
        rv = self.app.get("/")
        self.assertEqual(rv.data, "index_contents")

    def test_config(self):
        rv = self.app.get("/config")
        data = json.loads(rv.data)
        self.assertIn("ICON_DEFAULT", data)

    @patch("brew_view.controllers.ui_controller.thrift_context")
    def test_version_everything_works(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.getVersion = Mock(return_value="bartender_version")

        rv = self.app.get("/version")
        self.client_mock.getVersion.assert_called_once_with()

        data = json.loads(rv.data)
        self.assertEqual(data["brew_view_version"], __version__)
        self.assertEqual(data["bartender_version"], "bartender_version")
        self.assertEqual(data["current_api_version"], "v1")
        self.assertEqual(data["supported_api_versions"], ["v1"])

    @patch("brew_view.controllers.ui_controller.thrift_context")
    def test_version_fail_to_get_backend_version(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.getVersion = Mock(side_effect=ValueError)

        rv = self.app.get("/version")
        self.client_mock.getVersion.assert_called_once_with()

        data = json.loads(rv.data)
        self.assertEqual(data["brew_view_version"], __version__)
        self.assertEqual(data["bartender_version"], "unknown")
        self.assertEqual(data["current_api_version"], "v1")
        self.assertEqual(data["supported_api_versions"], ["v1"])
