import logging
import os
import unittest

from box import Box
from brewtils.errors import ValidationError
from brewtils.models import Principal
from mock import Mock, call, patch
from yapconf import YapconfSpec

import beer_garden as bg
from beer_garden.errors import ConfigurationError
from beer_garden.specification import SPECIFICATION


class BartenderTest(unittest.TestCase):
    def setUp(self):
        self.spec = YapconfSpec(SPECIFICATION)
        self.environment_copy = os.environ.copy()
        os.environ = {}

    def tearDown(self):
        os.environ = self.environment_copy

    @patch("bg_utils.setup_application_logging", Mock())
    def test_setup(self):
        bg.setup_bartender(self.spec, {})
        self.assertIsInstance(bg.config, Box)
        self.assertIsInstance(bg.logger, logging.Logger)

    def test_progressive_backoff(self):
        bg.logger = Mock()
        stop_mock = Mock(stopped=Mock(return_value=False))
        func_mock = Mock(side_effect=[False, False, False, True])

        bg.progressive_backoff(func_mock, stop_mock, "test_func")
        stop_mock.wait.assert_has_calls([call(0.1), call(0.2), call(0.4)])

    def test_progressive_backoff_max_timeout(self):
        bg.logger = Mock()
        stop_mock = Mock(stopped=Mock(return_value=False))

        side_effect = [False] * 10
        side_effect[-1] = True
        func_mock = Mock(side_effect=side_effect)

        bg.progressive_backoff(func_mock, stop_mock, "test_func")
        max_val = max([mock_call[0][0] for mock_call in stop_mock.wait.call_args_list])
        self.assertLessEqual(max_val, 30)

    @patch("bartender.bv_client")
    def test_ensure_admin(self, client_mock):
        client_mock.who_am_i.return_value = Principal(permissions=["bg-all"])
        bg.ensure_admin()

    @patch("bartender.config")
    @patch("bartender.bv_client")
    def test_ensure_admin_errors(self, client_mock, config_mock):
        client_mock.who_am_i.return_value = Principal(permissions=[])

        config_mock.web.username = None
        self.assertRaises(ConfigurationError, bg.ensure_admin)

        config_mock.web.username = "Bob"
        self.assertRaises(ConfigurationError, bg.ensure_admin)

        client_mock.who_am_i.side_effect = ValidationError
        self.assertRaises(ConfigurationError, bg.ensure_admin)
