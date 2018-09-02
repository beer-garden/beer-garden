import logging
import logging.config
import unittest

from box import Box
from mock import Mock, patch
from tornado.ioloop import IOLoop
from tornado.web import Application
from yapconf import YapconfSpec

import brew_view as bg
from brew_view.specification import SPECIFICATION


class BeerGardenTest(unittest.TestCase):
    def setUp(self):
        self.spec = YapconfSpec(SPECIFICATION)
        bg.config = None
        bg.io_loop = None
        bg.logger = None
        bg.thrift_context = None

    def tearDown(self):
        bg.config = None
        bg.io_loop = None
        bg.logger = None
        bg.thrift_context = None

    @patch('bg_utils.setup_application_logging', Mock())
    @patch('bg_utils.setup_database', Mock())
    @patch('brew_view.load_plugin_logging_config', Mock())
    @patch('brew_view.HTTPServer.listen', Mock())
    def test_setup_no_file(self):
        bg.setup(self.spec, {})
        self.assertIsInstance(bg.config, Box)
        self.assertIsInstance(bg.logger, logging.Logger)
        self.assertIsNotNone(bg.thrift_context)
        self.assertIsInstance(bg.io_loop, IOLoop)

    def test_setup_tornado_app(self):
        bg.config = self.spec.load_config({'web': {'url_prefix': '/'}})
        app = bg._setup_tornado_app()
        self.assertIsInstance(app, Application)

    def test_setup_tornado_app_debug_true(self):
        bg.config = self.spec.load_config({'debug_mode': True,
                                           'web': {'url_prefix': '/'}})
        app = bg._setup_tornado_app()
        self.assertTrue(app.settings.get('autoreload'))

    def test_setup_ssl_context_ssl_not_enabled(self):
        bg.config = self.spec.load_config({'web': {'ssl': {'enabled': False}}})
        server_ssl, client_ssl = bg._setup_ssl_context()
        self.assertIsNone(server_ssl)
        self.assertIsNone(client_ssl)

    @patch('brew_view.ssl')
    def test_setup_ssl_context_ssl_enabled(self, ssl_mock):
        bg.config = self.spec.load_config({
            'web': {
                'ssl': {
                    'enabled': True,
                    'public_key': '/path/to/public.key',
                    'private_key': '/path/to/private.key',
                    'ca_cert': '/path/to/ca/file',
                    'ca_path': '/path/to/ca/path',
                }
            }
        })
        server_context = Mock()
        client_context = Mock()
        ssl_mock.create_default_context.side_effect = [server_context, client_context]

        bg._setup_ssl_context()
        server_context.load_cert_chain.assert_called_with(certfile='/path/to/public.key',
                                                          keyfile='/path/to/private.key')
        client_context.load_cert_chain.assert_called_with(certfile='/path/to/public.key',
                                                          keyfile='/path/to/private.key')
        server_context.load_verify_locations.assert_called_with(cafile='/path/to/ca/file',
                                                                capath='/path/to/ca/path')
        client_context.load_verify_locations.assert_called_with(cafile='/path/to/ca/file',
                                                                capath='/path/to/ca/path')

    @patch('brew_view.PluginLoggingLoader')
    def test_load_plugin_logging_config(self, PluginLoggingLoaderMock):
        app_config = Mock()
        app_config.plugin_logging.config_file = "plugin_log_config"
        app_config.plugin_logging.level = "INFO"

        bg.app_logging_config = "app_logging_config"
        loader_mock = Mock()
        PluginLoggingLoaderMock.return_value = loader_mock
        bg.load_plugin_logging_config(app_config)
        loader_mock.load.assert_called_with(
            filename="plugin_log_config",
            level="INFO",
            default_config="app_logging_config"
        )
