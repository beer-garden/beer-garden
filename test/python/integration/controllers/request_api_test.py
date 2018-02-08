import unittest

from mock import Mock, patch

import brew_view
from bg_utils.models import Request
from bg_utils.parser import BeerGardenSchemaParser


@unittest.skip('TODO')
class RequestAPITest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        # brew_view.load_app(environment="test")

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.default_request = Request(system='foo', command='bar', parameters={'baz': 'bat'}, output='output',
                                       status='CREATED')
        self.default_request.validate_backend = Mock()

        objects_patch = patch('bg_utils.models.Request.objects')
        self.addCleanup(objects_patch.stop)
        self.objects_mock = objects_patch.start()
        self.objects_mock.return_value = None
        self.objects_mock.get = Mock(return_value=self.default_request)

    def test_get(self):
        response = self.app.get("/api/v1/requests/id")

        self.assertEqual(200, response.status_code)
        self.objects_mock.get.assert_called_with(id='id')
        self.objects_mock.assert_called_with(parent=self.default_request)

        response_request = BeerGardenSchemaParser().parse_request(response.data, from_string=True)
        self.assertEqual(self.default_request.system, response_request.system)
        self.assertEqual(self.default_request.command, response_request.command)
        self.assertDictEqual(self.default_request.parameters, response_request.parameters)
        self.assertEqual(self.default_request.output, response_request.output)
        self.assertEqual(self.default_request.status, response_request.status)
