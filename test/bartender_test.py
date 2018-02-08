import logging
import os
import unittest

from mock import Mock, patch, call
from box import Box
from yapconf import YapconfSpec

import bartender as bg
from bartender.app import BartenderApp
from bartender.specification import SPECIFICATION, get_default_logging_config


class BartenderTest(unittest.TestCase):

    def setUp(self):
        self.spec = YapconfSpec(SPECIFICATION)
        self.environment_copy = os.environ.copy()
        os.environ = {}

    def tearDown(self):
        os.environ = self.environment_copy

    @patch('bg_utils.setup_application_logging', Mock())
    @patch('bg_utils.setup_database', Mock())
    @patch('bartender._progressive_backoff', Mock())
    def test_setup_no_file_given(self):
        bg.setup_bartender(self.spec, {})
        self.assertIsInstance(bg.config, Box)
        self.assertIsInstance(bg.logger, logging.Logger)
        self.assertIsInstance(bg.application, BartenderApp)

    @patch('bartender._progressive_backoff', Mock())
    @patch('bg_utils.setup_database', Mock())
    @patch('bartender.logging.config')
    @patch('bartender.open')
    @patch('json.load')
    def test_setup_with_config_file(self, json_mock, open_mock, logging_mock):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        fake_config = {"log_level": "WARN"}
        json_mock.return_value = fake_config
        bg.setup_bartender(self.spec, {'config': 'path/to/config.json'})
        self.assertEqual(open_mock.call_count, 1)
        json_mock.assert_called_with(fake_file)
        logging_mock.dictConfig.assert_called_with(get_default_logging_config('WARN', None))

    @patch('bartender.time')
    def test_progressive_backoff(self, time_mock):
        bg.logger = Mock()
        func_mock = Mock(side_effect=[False, False, False, True])

        bg._progressive_backoff(func_mock, 'test_func')
        time_mock.sleep.assert_has_calls([call(0.1), call(0.2), call(0.4)])

    @patch('bartender.time')
    def test_progressive_backoff_max_timeout(self, time_mock):
        bg.logger = Mock()

        side_effect = [False]*10
        side_effect[-1] = True
        func_mock = Mock(side_effect=side_effect)

        bg._progressive_backoff(func_mock, 'test_func')
        max_val = max([mock_call[0][0] for mock_call in time_mock.sleep.call_args_list])
        self.assertLessEqual(max_val, 30)

    def test_connect_to_brew_view_success(self):
        client_mock = Mock()
        bg.bv_client = client_mock
        bg.logger = Mock()

        ret_val = bg._connect_to_brew_view()
        client_mock.find_systems.assert_called_once()
        self.assertTrue(ret_val)

    def test_connect_to_brew_view_failure(self):
        from requests.exceptions import RequestException

        client_mock = Mock(find_systems=Mock(side_effect=RequestException))
        bg.bv_client = client_mock
        bg.logger = Mock()

        ret_val = bg._connect_to_brew_view()
        client_mock.find_systems.assert_called_once()
        self.assertFalse(ret_val)
