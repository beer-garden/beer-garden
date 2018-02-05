import unittest
import warnings

from mock import Mock, patch

from bg_utils.local_plugin import MultiThreadedLocalPlugin, SimpleLocalPlugin


@patch('bg_utils.local_plugin.super', Mock())
class SimpleLocalPluginTest(unittest.TestCase):

    def test_deprecation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            SimpleLocalPlugin(Mock())
            self.assertEqual(1, len(w))

            warning = w[0]
            self.assertEqual(warning.category, DeprecationWarning)
            self.assertIn("'SimpleLocalPlugin'", str(warning))
            self.assertIn("'LocalPlugin'", str(warning))
            self.assertIn('3.0', str(warning))


@patch('bg_utils.local_plugin.super', Mock())
class MultiThreadedLocalPluginTest(unittest.TestCase):

    def test_deprecation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            MultiThreadedLocalPlugin(Mock())
            self.assertEqual(1, len(w))

            warning = w[0]
            self.assertEqual(warning.category, DeprecationWarning)
            self.assertIn("'MultiThreadedLocalPlugin'", str(warning))
            self.assertIn("LocalPlugin", str(warning))
            self.assertIn('3.0', str(warning))
