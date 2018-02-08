import unittest

from bg_utils.fields import DummyField


class DummyFieldTest(unittest.TestCase):

    def test_to_python(self):
        field = DummyField()
        self.assertEqual('value', field.to_python('value'))

    def test_to_mongo(self):
        field = DummyField()
        self.assertIsNone(field.to_mongo('value'))
