import logging
import logging.config
import unittest

from box import Box
from mock import Mock, patch
from tornado.ioloop import IOLoop
from tornado.web import Application
from yapconf import YapconfSpec

import brew_view as bg
from brew_view.specification import SPECIFICATION, get_default_logging_config


class BeerGardenTest(unittest.TestCase):
    def setUp(self):
        self.spec = YapconfSpec(SPECIFICATION)
        bg.config = None
        bg.application = None
        bg.logger = None
        bg.thrift_context = None

    def tearDown(self):
        bg.config = None
        bg.application = None
        bg.logger = None
        bg.thrift_context = None

    @patch('bg_utils.setup_application_logging', Mock())
    @patch('bg_utils.setup_database', Mock())
    @patch('brew_view.load_plugin_logging_config', Mock())
    def test_setup_brew_view_no_file_given(self):
        bg.setup_brew_view(self.spec, {})
        self.assertIsInstance(bg.config, Box)
        self.assertIsInstance(bg.logger, logging.Logger)
        self.assertIsNotNone(bg.thrift_context)
        self.assertIsInstance(bg.application, IOLoop)

    @patch('bg_utils.setup_database', Mock())
    @patch('brew_view.load_plugin_logging_config', Mock())
    @patch('brew_view.setup_application', Mock())
    @patch('brew_view.logging.config')
    @patch('brew_view.open')
    @patch('json.load')
    def test_setup_brew_view_with_file_given(self, json_mock, open_mock, logging_mock):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        fake_config = {"log_level": "WARN"}
        json_mock.return_value = fake_config
        bg.setup_brew_view(self.spec, {'config': 'path/to/config.json'})
        self.assertEqual(open_mock.call_count, 1)
        json_mock.assert_called_with(fake_file)
        logging_mock.dictConfig.assert_called_with(get_default_logging_config('WARN', None))

    def test_setup_tornado_app(self):
        config = self.spec.load_config({'application_name': 'Beergarden', 'url_prefix': '/'})
        app = bg._setup_tornado_app(config)
        self.assertIsInstance(app, Application)

    def test_setup_tornado_app_debug_true(self):
        config = self.spec.load_config({'debug_mode': True,
                                        'application_name': 'Beergarden',
                                        'url_prefix': '/'})
        app = bg._setup_tornado_app(config)
        self.assertTrue(app.settings.get('autoreload'))

    def test_setup_ssl_context_ssl_not_enabled(self):
        config = self.spec.load_config({'ssl_enabled': False})
        server_ssl, client_ssl = bg._setup_ssl_context(config)
        self.assertIsNone(server_ssl)
        self.assertIsNone(client_ssl)

    @patch('brew_view.ssl')
    def test_setup_ssl_context_ssl_enabled(self, ssl_mock):
        config = self.spec.load_config({
            'ssl_enabled': True,
            'ssl_public_key': '/path/to/public.key',
            'ssl_private_key': '/path/to/private.key',
            'ca_cert': '/path/to/ca/file',
            'ca_path': '/path/to/ca/path',
        })
        server_context = Mock()
        client_context = Mock()
        ssl_mock.create_default_context.side_effect = [server_context, client_context]

        bg._setup_ssl_context(config)
        server_context.load_cert_chain.assert_called_with(certfile='/path/to/public.key',
                                                          keyfile='/path/to/private.key')
        client_context.load_cert_chain.assert_called_with(certfile='/path/to/public.key',
                                                          keyfile='/path/to/private.key')
        server_context.load_verify_locations.assert_called_with(cafile='/path/to/ca/file',
                                                                capath='/path/to/ca/path')
        client_context.load_verify_locations.assert_called_with(cafile='/path/to/ca/file',
                                                                capath='/path/to/ca/path')

    @patch('brew_view.ssl')
    def test_setup_ssl_context_bad_client_verify_value(self, ssl_mock):
        config = self.spec.load_config({'ssl_enabled': True,
                                        'client_cert_verify': 'BAD'})

        self.assertRaises(Exception, bg._setup_ssl_context, config)

    @patch('brew_view.PluginLoggingLoader')
    def test_load_plugin_logging_config(self, PluginLoggingLoaderMock):
        app_config = Mock(plugin_log_config="plugin_log_config",
                          plugin_log_level="INFO")
        bg.app_log_config = "app_log_config"
        loader_mock = Mock()
        PluginLoggingLoaderMock.return_value = loader_mock
        bg.load_plugin_logging_config(app_config)
        loader_mock.load.assert_called_with(filename="plugin_log_config",
                                            level="INFO",
                                            default_config="app_log_config")
