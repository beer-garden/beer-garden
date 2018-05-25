import unittest
import json

from . import TestHandlerBase
from mock import patch


class LoggingApiTest(TestHandlerBase):

    def setUp(self):
        super(LoggingApiTest, self).setUp()

    @patch('brew_view.controllers.logging_api.BeerGardenSchemaParser.serialize_logging_config')
    def test_get_config(self, serialize_mock):
        serialize_mock.return_value = "serialized_logging_config"

        response = self.fetch("/api/v1/config/logging")
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_logging_config', response.body.decode('utf-8'))

    @patch('brew_view.load_plugin_logging_config')
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_logging_config')
    def test_patch_reload(self, serialize_mock, load_mock):
        serialize_mock.return_value = 'serialized_logging_config'

        response = self.fetch('/api/v1/config/logging', method='PATCH',
                              body='{"operations": [{"operation": "reload"}]}',
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_logging_config', response.body.decode('utf-8'))
        self.assertEqual(load_mock.call_count, 1)

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_logging_config')
    def test_patch_invalid_operation(self, serialize_mock):
        body = json.dumps({"operations": [{"operation": "INVALID"}]})
        serialize_mock.return_value = 'serialized_logging_config'

        response = self.fetch('/api/v1/config/logging', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(400, response.code)


if __name__ == '__main__':
    unittest.main()
