import logging
import os
import unittest

from mock import Mock, patch

import bartender.local_plugins.logger as bglogging
from bartender.local_plugins.logger import PluginHandler


class PluginHandlerTest(unittest.TestCase):

    def test_init_no_log_directory(self):
        fake_factory = Mock()
        PluginHandler(fake_factory, 'name', log_directory=None)
        fake_factory.assert_called_with(maxBytes=10485760, backupCount=5)

    def test_init_with_log_directory(self):
        fake_factory = Mock()
        PluginHandler(fake_factory, 'name', log_directory="/path")
        fake_factory.assert_called_with(filename=os.path.join("/path", "name.log"),
                                        maxBytes=10485760, backupCount=5)

    def test_getattr_true(self):
        fake_handler = Mock()
        fake_factory = Mock(return_value=fake_handler)
        handler = PluginHandler(fake_factory, 'name')
        handler.foo()
        fake_handler.foo.assert_called_with()

    def test_getattr_false(self):
        fake_handler = Mock(spec=[])
        fake_factory = Mock(return_value=fake_handler)
        handler = PluginHandler(fake_factory, 'name')
        self.assertRaises(AttributeError, handler.__getattr__, 'foo')


class LoggingTest(unittest.TestCase):

    def setUp(self):
        log = logging.getLogger('foo')
        if len(log.handlers) > 0:
            for h in log.handlers:
                log.removeHandler(h)

    def tearDown(self):
        self.fake_formatter = None

    def test_get_plugin_logger_already_instantiated(self):
        log = bglogging.getPluginLogger('foo', formatted=False)
        log2 = bglogging.getPluginLogger('foo', formatted=False)
        self.assertEqual(log, log2)

    def test_get_plugin_logger_no_log_directory(self):
        log = bglogging.getPluginLogger('foo')
        self.assertEqual(len(log.handlers), 1)
        self.assertEqual(log.handlers[0], logging.getLogger().handlers[0])

    @patch('bartender.local_plugins.logger.PluginHandler')
    def test_get_plugin_logger_with_log_directory_and_formatted(self, handler_mock):
        def side_effect(f):
            self.fake_formatter = f

        fake_handler = Mock(setFormatter=Mock(side_effect=side_effect))
        handler_mock.return_value = fake_handler

        log = bglogging.getPluginLogger('foo', formatted=True, log_directory="log_directory")
        fake_handler.setLevel.assert_called_with(logging.INFO)
        self.assertEqual(log.propagate, False)
        self.assertEqual(len(log.handlers), 1)
        self.assertEqual(self.fake_formatter._fmt,
                         '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    @patch('bartender.local_plugins.logger.PluginHandler')
    def test_get_plugin_logger_with_log_directory_not_formatted(self, handler_mock):
        def side_effect(f):
            self.fake_formatter = f

        fake_handler = Mock(setFormatter=Mock(side_effect=side_effect))
        handler_mock.return_value = fake_handler

        log = bglogging.getPluginLogger('foo', formatted=False, log_directory="log_directory")
        fake_handler.setLevel.assert_called_with(logging.INFO)
        self.assertEqual(log.propagate, False)
        self.assertEqual(len(log.handlers), 1)
        self.assertEqual(self.fake_formatter._fmt, '%(asctime)s - %(message)s')
