from mock import MagicMock, Mock, PropertyMock, patch
from tornado.gen import Future

import bg_utils
from . import TestHandlerBase


class RequestListAPITest(TestHandlerBase):

    def setUp(self):
        self.request_mock = MagicMock(name='Request Mock')
        self.request_mock.only.return_value = self.request_mock
        self.request_mock.search_text.return_value = self.request_mock
        self.request_mock.order_by.return_value = self.request_mock
        self.request_mock.id = 'id'
        self.request_mock.instance_name = 'default'
        self.request_mock.__getitem__.return_value = self.request_mock
        self.request_mock.__len__.return_value = 1

        mongo_patcher = patch('brew_view.controllers.request_list_api.Request.objects')
        self.addCleanup(mongo_patcher.stop)
        self.mongo_mock = mongo_patcher.start()
        self.mongo_mock.count.return_value = 1

        serialize_patcher = patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.serialize_request')
        self.addCleanup(serialize_patcher.stop)
        self.serialize_mock = serialize_patcher.start()
        self.serialize_mock.return_value = 'serialized_request'

        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock), __exit__=Mock(return_value=False))
        self.future_mock = Future()

        super(RequestListAPITest, self).setUp()

    @patch('brew_view.controllers.request_list_api.RequestListAPI._get_requests')
    def test_get(self, get_requests_mock):
        get_requests_mock.return_value = (['request'], 1, None)

        response = self.fetch('/api/v1/requests?draw=1')
        self.assertEqual(200, response.code)
        self.serialize_mock.assert_called_once_with(['request'], many=True, only=None, to_string=True)
        self.assertEqual('0', response.headers['start'])
        self.assertEqual('1', response.headers['length'])
        self.assertEqual('1', response.headers['recordsFiltered'])
        self.assertEqual('1', response.headers['recordsTotal'])
        self.assertEqual('1', response.headers['draw'])

    @patch('brew_view.controllers.request_list_api.System.objects')
    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_json(self, context_mock, parse_mock, system_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_result(None)
        parse_mock.return_value = self.request_mock
        self.mongo_mock.get.return_value = self.request_mock

        instance_mock = Mock(status='RUNNING')
        type(instance_mock).name = PropertyMock(return_value='default')
        system_mock.get.return_value = Mock(instances=[instance_mock])

        response = self.fetch('/api/v1/requests', method='POST', body='', headers={'content-type': 'application/json'})
        self.assertEqual(201, response.code)
        self.assertEqual('RUNNING', response.headers['Instance-Status'])
        self.assertTrue(self.request_mock.save.called)
        self.client_mock.processRequest.assert_called_once_with(self.request_mock.id)

    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_invalid(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_exception(bg_utils.bg_thrift.InvalidRequest())
        parse_mock.return_value = self.request_mock

        response = self.fetch('/api/v1/requests', method='POST', body='', headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)
        self.assertTrue(self.request_mock.delete.called)
        self.assertTrue(self.client_mock.processRequest.called)

    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.future_mock.set_exception(Exception())
        parse_mock.return_value = self.request_mock

        response = self.fetch('/api/v1/requests', method='POST', body='', headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)
        self.assertTrue(self.request_mock.delete.called)

    def test_post_no_content_type(self):
        response = self.fetch('/api/v1/requests', method='POST', body='', headers={'content-type': 'text/plain'})
        self.assertEqual(response.code, 400)

    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_instance_status_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_result(None)
        parse_mock.return_value = self.request_mock
        self.mongo_mock.get.return_value = self.request_mock

        response = self.fetch('/api/v1/requests', method='POST', body='', headers={'content-type': 'application/json'})
        self.assertEqual(201, response.code)
        self.assertIn('Instance-Status', response.headers)
        self.assertEqual('UNKNOWN', response.headers['Instance-Status'])
