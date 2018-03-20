import json

from mock import Mock, patch
from mongoengine.errors import DoesNotExist

from . import TestHandlerBase


class RequestAPITest(TestHandlerBase):

    def setUp(self):
        self.request_mock = Mock()

        mongo_patcher = patch('mongoengine.queryset.manager.QuerySetManager.__get__')
        self.addCleanup(mongo_patcher.stop)
        self.get_mock = mongo_patcher.start()
        self.get_mock.return_value.get.return_value = self.request_mock

        serialize_patcher = patch(
            'brew_view.controllers.request_api.BeerGardenSchemaParser.serialize_request'
        )
        self.addCleanup(serialize_patcher.stop)
        self.serialize_mock = serialize_patcher.start()
        self.serialize_mock.return_value = 'serialized_request'

        super(RequestAPITest, self).setUp()

    def test_get(self):
        response = self.fetch('/api/v1/requests/id')
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))

    def test_patch_replace_duplicate(self):
        body = json.dumps({
                "operations": [
                        {
                            "operation": "replace",
                            "path": "/output",
                            "value": "output"
                        },
                        {
                            "operation": "replace",
                            "path": "/status",
                            "value": "SUCCESS"
                        },
                ]
        })
        self.request_mock.status = "SUCCESS"
        self.request_mock.output = "output"

        response = self.fetch('/api/v1/requests/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))
        self.assertEqual("SUCCESS", self.request_mock.status)
        self.assertEqual("output", self.request_mock.output)
        self.assertTrue(self.request_mock.save.called)

    def test_patch_replace_status(self):
        body = json.dumps({"operations": [{"operation": "replace", "path": "/status",
                                           "value": "SUCCESS"}]})

        response = self.fetch('/api/v1/requests/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))
        self.assertEqual("SUCCESS", self.request_mock.status)
        self.assertTrue(self.request_mock.save.called)

    def test_patch_replace_output(self):
        body = json.dumps({"operations": [{"operation": "replace", "path": "/output",
                                           "value": "output"}]})

        response = self.fetch('/api/v1/requests/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))
        self.assertEqual("output", self.request_mock.output)
        self.assertTrue(self.request_mock.save.called)

    def test_patch_replace_error_class(self):
        body = json.dumps({"operations": [{"operation": "replace", "path": "/error_class",
                                           "value": "error"}]})

        response = self.fetch('/api/v1/requests/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))
        self.assertEqual("error", self.request_mock.error_class)
        self.assertTrue(self.request_mock.save.called)

    def test_patch_replace_bad_status(self):
        body = json.dumps({"operations": [{"operation": "replace", "path": "/status",
                                           "value": "bad"}]})
        response = self.fetch('/api/v1/requests/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)

    def test_patch_update_output_for_complete_request(self):
        self.request_mock.status = "SUCCESS"
        body = json.dumps({"operations": [{"operation": "replace", "path": "/output",
                                           "value": "shouldnt work"}]})
        response = self.fetch("/api/v1/requests/id", method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)

    def test_patch_no_system(self):
        self.get_mock.return_value.get.side_effect = DoesNotExist

        response = self.fetch('/api/v1/requests/id', method='PATCH',
                              body='{"operations": [{"operation": "fake"}]}',
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)

    def test_patch_replace_bad_path(self):
        body = json.dumps({"operations": [{"operation": "replace", "path": "/bad",
                                           "value": "error"}]})
        response = self.fetch('/api/v1/requests/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)

    def test_patch_bad_operation(self):
        response = self.fetch('/api/v1/requests/id', method='PATCH',
                              body='{"operations": [{"operation": "fake"}]}',
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)
