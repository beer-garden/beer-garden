import logging
import os
import unittest

import requests.exceptions
from box import Box
from mock import Mock, call, patch
from yapconf import YapconfSpec

import bartender as bg
from bartender.specification import SPECIFICATION


class BartenderTest(unittest.TestCase):

    def setUp(self):
        self.spec = YapconfSpec(SPECIFICATION)
        self.environment_copy = os.environ.copy()
        os.environ = {}

    def tearDown(self):
        os.environ = self.environment_copy

    @patch('bg_utils.setup_application_logging', Mock())
    @patch('bg_utils.setup_database', Mock())
    def test_setup(self):
        bg.setup_bartender(self.spec, {})
        self.assertIsInstance(bg.config, Box)
        self.assertIsInstance(bg.logger, logging.Logger)

    def test_progressive_backoff(self):
        bg.logger = Mock()
        stop_mock = Mock(stopped=Mock(return_value=False))
        func_mock = Mock(side_effect=[False, False, False, True])

        bg.progressive_backoff(func_mock, stop_mock, 'test_func')
        stop_mock.wait.assert_has_calls([call(0.1), call(0.2), call(0.4)])

    def test_progressive_backoff_max_timeout(self):
        bg.logger = Mock()
        stop_mock = Mock(stopped=Mock(return_value=False))

        side_effect = [False]*10
        side_effect[-1] = True
        func_mock = Mock(side_effect=side_effect)

        bg.progressive_backoff(func_mock, stop_mock, 'test_func')
        max_val = max([mock_call[0][0] for mock_call in stop_mock.wait.call_args_list])
        self.assertLessEqual(max_val, 30)

    def test_connect_to_brew_view_success(self):
        client_mock = Mock()
        bg.bv_client = client_mock
        bg.logger = Mock()

        self.assertTrue(bg.connect_to_brew_view())
        client_mock.find_systems.assert_called_once()

    def test_connect_to_brew_view_failure(self):
        client_mock = Mock(find_systems=Mock(side_effect=requests.exceptions.ConnectionError))
        bg.bv_client = client_mock
        bg.logger = Mock()

        self.assertFalse(bg.connect_to_brew_view())
        client_mock.find_systems.assert_called_once()

    def test_connect_to_brew_view_error(self):
        client_mock = Mock(find_systems=Mock(side_effect=requests.exceptions.SSLError))
        bg.bv_client = client_mock
        bg.logger = Mock()

        self.assertRaises(requests.exceptions.SSLError, bg.connect_to_brew_view)
