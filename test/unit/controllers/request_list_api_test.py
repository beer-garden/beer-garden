import json

import pytest
from mock import MagicMock, Mock, PropertyMock, patch
from mongoengine import connect
from tornado.gen import Future

import bg_utils
import brew_view
from brew_view.controllers import RequestListAPI
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

        serialize_patcher = patch(
            'brew_view.controllers.request_list_api.BeerGardenSchemaParser.serialize_request'
        )
        self.addCleanup(serialize_patcher.stop)
        self.serialize_mock = serialize_patcher.start()
        self.serialize_mock.return_value = 'serialized_request'

        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock),
                                      __exit__=Mock(return_value=False))
        self.future_mock = Future()

        super(RequestListAPITest, self).setUp()

    @patch('brew_view.controllers.request_list_api.RequestListAPI._get_query_set')
    def test_get(self, get_query_set_mock):
        query_set = MagicMock()
        query_set.count.return_value = 1
        query_set.__getitem__ = lambda *_: ['request']
        get_query_set_mock.return_value = (query_set, None)

        response = self.fetch('/api/v1/requests?draw=1')
        self.assertEqual(200, response.code)
        self.serialize_mock.assert_called_once_with(['request'], many=True, only=None,
                                                    to_string=True)
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

        response = self.fetch('/api/v1/requests', method='POST', body='',
                              headers={'content-type': 'application/json'})
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

        response = self.fetch('/api/v1/requests', method='POST', body='',
                              headers={'content-type': 'application/json'})
        self.assertEqual(response.code, 400)
        self.assertTrue(self.request_mock.delete.called)
        self.assertTrue(self.client_mock.processRequest.called)

    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_publishing_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_exception(bg_utils.bg_thrift.PublishException())
        parse_mock.return_value = self.request_mock

        response = self.fetch('/api/v1/requests', method='POST', body='',
                              headers={'content-type': 'application/json'})
        self.assertEqual(response.code, 502)
        self.assertTrue(self.request_mock.delete.called)

    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.future_mock.set_exception(Exception())
        parse_mock.return_value = self.request_mock

        response = self.fetch('/api/v1/requests', method='POST', body='',
                              headers={'content-type': 'application/json'})
        self.assertEqual(response.code, 500)
        self.assertTrue(self.request_mock.delete.called)

    def test_post_no_content_type(self):
        response = self.fetch('/api/v1/requests', method='POST', body='',
                              headers={'content-type': 'text/plain'})
        self.assertEqual(response.code, 400)

    @patch('brew_view.controllers.request_list_api.BeerGardenSchemaParser.parse_request')
    @patch('brew_view.controllers.request_list_api.thrift_context')
    def test_post_instance_status_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_result(None)
        parse_mock.return_value = self.request_mock
        self.mongo_mock.get.return_value = self.request_mock

        response = self.fetch('/api/v1/requests', method='POST', body='',
                              headers={'content-type': 'application/json'})
        self.assertEqual(201, response.code)
        self.assertIn('Instance-Status', response.headers)
        self.assertEqual('UNKNOWN', response.headers['Instance-Status'])


@pytest.fixture
def mongo_mock():
    connect('mongotest', host='mongomock://localhost')


@pytest.mark.usefixtures('mongo_mock')
class TestRequestListAPI(object):

    @pytest.fixture
    def columns(self):

        def _factory(search=None):
            search = search or {}

            columns = [
                {
                    'data': 'command',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('command', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'system',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('system', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'instance_name',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('instance_name', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'status',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('status', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'created_at',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('created_at', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'comment',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('comment', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'metadata',
                    'name': '',
                    'searchable': True,
                    'orderable': True,
                    'search': {
                        'value': search.get('metadata', ''),
                        'regex': False,
                    },
                },
                {
                    'data': 'id',
                },
            ]

            return [json.dumps(column) for column in columns]

        return _factory

    @pytest.fixture
    def order(self):

        def _factory(order_column):
            if order_column is not None:
                return [json.dumps({"column": order_column, "dir": "desc"})]
            return None

        return _factory

    @pytest.fixture
    def handler(self, monkeypatch):
        monkeypatch.setattr(brew_view, 'config', Mock())
        return RequestListAPI(MagicMock(), MagicMock())

    @pytest.mark.parametrize('order_column,search,index', [
        # Neither
        (None, None, 'parent_index'),

        # Only sorting
        (0, None, 'parent_command_index'),
        (1, None, 'parent_system_index'),
        (2, None, 'parent_instance_name_index'),
        (3, None, 'parent_status_index'),
        (4, None, 'parent_created_at_index'),

        # Only filtering
        (None, {'command': 'say'}, 'parent_command_index'),
        (None, {'system': 'test'}, 'parent_system_index'),
        (None, {'instance_name': 'say'}, 'parent_instance_name_index'),
        (None, {'status': 'SUCCESS'}, 'parent_status_index'),
        (None, {'created_at': 'start~stop'}, 'parent_created_at_index'),

        # Both, but only applicable for created_at sorting
        (4, {'command': 'say'}, 'parent_created_at_command_index'),
        (4, {'system': 'test'}, 'parent_created_at_system_index'),
        (4, {'instance_name': 'say'}, 'parent_created_at_instance_name_index'),
        (4, {'status': 'SUCCESS'}, 'parent_created_at_status_index'),
        (4, {'created_at': 'start~stop'}, 'parent_created_at_index'),
    ])
    def test_order_index_hints(
            self, monkeypatch, handler, columns, order, order_column, search,
            index):

        args = {
            'columns': columns(search),
            'order': order(order_column)
        }

        if order_column is None:
            del args['order']

        monkeypatch.setattr(handler.request, 'query_arguments', args)

        query_set, fields = handler._get_query_set()
        assert index == query_set._hint
