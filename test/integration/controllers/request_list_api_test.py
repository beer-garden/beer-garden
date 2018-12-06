import json
import unittest
import urllib

from mock import Mock, MagicMock, patch
from mongoengine import Q

import brew_view
from bg_utils.mongo.models import Request


@unittest.skip('TODO')
class RequestListAPITest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
        # brew_view.load_app("test")

    def setUp(self):
        brew_view.backend = Mock()
        brew_view.transport = Mock()
        self.default_request = Request(system='foo', command='bar', parameters={'baz': 'bat'}, output='output',
                                       status='CREATED')
        self.default_request.validate_backend = Mock()
        self.app = brew_view.app.test_client()

    def tearDown(self):
        brew_view.backend = None
        brew_view.transport = None

    def _datatables_query(self, columns=None, query_params=None):
        # Datatables does this awesome thing where it sends some parameters as urlencoded json
        # AND every column has key 'columns'
        columns = columns or [
            {'data': 'command', 'name': '', 'searchable': True,
                'orderable': True, 'search': {'value': '', 'regex': False}},
            {'data': 'system', 'name': '', 'searchable': True,
                'orderable': True, 'search': {'value': 'tst', 'regex': False}},
            {'data': 'created_at', 'name': '', 'searchable': True, 'orderable': True,
                'search': {'value': '6/1/2016~6/2/2016', 'regex': False}}
        ]

        query_params = query_params or {
            'draw': '1',
            'start': '0',
            'length': '10',
            'order': json.dumps({'column': 0, 'dir': 'desc'}),
            'search': json.dumps({'value': 'test', 'regex': 'false'})
        }

        query_string = urllib.urlencode(query_params)

        for column in columns:
            query_string += '&columns=' + urllib.quote(json.dumps(column))

        return query_string

    def _get_query_mock(self):
        query_mock = MagicMock(name='QueryMock')
        query_mock.only.return_value = query_mock
        query_mock.search_text.return_value = query_mock
        query_mock.order_by.return_value = query_mock

        return query_mock

    @patch('bg_utils.mongo.models.Request.objects')
    def test_get_emtpy(self, objects_mock):
        fake_list = Mock(__iter__=Mock(return_value=[]),
                         __getitem__=Mock(return_value=[]))
        objects_mock.return_value = fake_list

        rv = self.app.get('/api/v1/requests')
        data = json.loads(rv.data)

        # self.assertEqual(Request.objects.call_count, 1)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 0)

    @patch('bg_utils.mongo.models.Request.objects')
    def test_get_with_results_no_headers(self, all_mock):
        fake_list = Mock(__iter__=Mock(return_value=[self.default_request]),
                         __getitem__=Mock(return_value=[self.default_request]))
        all_mock.return_value = fake_list
        rv = self.app.get('/api/v1/requests')
        data = json.loads(rv.data)

        self.assertEqual(Request.objects.call_count, 1)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 1)

    def test_get_response_headers(self):
        query_mock = self._get_query_mock()

        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            rv = self.app.get('/api/v1/requests')
            self.assertIn('start', rv.headers)
            self.assertIn('length', rv.headers)
            self.assertIn('recordsTotal', rv.headers)
            self.assertIn('recordsFiltered', rv.headers)
            self.assertEqual(rv.status_code, 200)

    def test_get_response_headers_datatables(self):

        query_params = {
            'draw': '1',
            'start': '0',
            'length': '10'
        }

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            rv = self.app.get('/api/v1/requests?' +
                              self._datatables_query(query_params=query_params))
            self.assertEqual(query_params['start'], rv.headers['start'])
            self.assertEqual('0', rv.headers['length'])
            self.assertEqual(query_params['draw'], rv.headers['draw'])
            self.assertIn('recordsTotal', rv.headers)
            self.assertIn('recordsFiltered', rv.headers)
            self.assertEqual(rv.status_code, 200)

    def test_get_with_columns(self):
        columns = [
            {'data': 'command', 'name': '', 'searchable': True,
                'orderable': True, 'search': {'value': '', 'regex': False}},
            {'data': 'created_at', 'name': '', 'searchable': True, 'orderable': True,
                'search': {'value': '6/1/2016~6/2/2016', 'regex': False}}
        ]

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            self.app.get('/api/v1/requests?' +
                         self._datatables_query(columns=columns))

            query_mock.only.assert_called_once_with('command', 'created_at')

    def test_get_with_system_column(self):
        columns = [
            {'data': 'command', 'name': '', 'searchable': True,
                'orderable': True, 'search': {'value': '', 'regex': False}},
            {'data': 'system', 'name': '', 'searchable': True,
                'orderable': True, 'search': {'value': 'tst', 'regex': False}}
        ]

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            self.app.get('/api/v1/requests?' +
                         self._datatables_query(columns=columns))

            query_mock.only.assert_called_once_with(
                'command', 'system', 'instance_name')

    def test_no_search_params(self):

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock) as search_mock:
            self.app.get('/api/v1/requests')

            self.assertEqual(search_mock.call_args[0][0].query, Q(parent__exists=False).query)

    def test_search_params(self):

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock) as search_mock:
            self.app.get('/api/v1/requests?' + self._datatables_query())

            self.assertFalse(search_mock.call_args[0][0].empty)

    def test_include_children(self):

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock) as search_mock:
            self.app.get('/api/v1/requests?' + 'include_children=true')

            self.assertTrue(search_mock.call_args[0][0].empty)

    def test_exclude_children(self):

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock) as search_mock:
            self.app.get('/api/v1/requests?' + 'include_children=false')

            self.assertEqual(search_mock.call_args[0][0].query, Q(parent__exists=False).query)

    def test_get_overall_search(self):
        search_value = 'search this!'
        query_params = {
            'search': json.dumps({'value': search_value, 'regex': 'false'})
        }

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            self.app.get('/api/v1/requests?' +
                         self._datatables_query(query_params=query_params))

            query_mock.search_text.assert_called_once_with("\"" + search_value + "\"")

    def test_get_order_by_asc(self):
        order_column_name = 'command'

        columns = [
            {'data': order_column_name, 'name': '', 'searchable': True, 'orderable': True,
             'search': {'value': '', 'regex': False}}
        ]
        query_params = {
            'order': json.dumps({'column': 0, 'dir': 'asc'})
        }

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            self.app.get('/api/v1/requests?' +
                         self._datatables_query(columns=columns, query_params=query_params))

            query_mock.order_by.assert_called_once_with(order_column_name)

    def test_get_order_by_desc(self):
        order_column_name = 'command'

        columns = [
            {'data': order_column_name, 'name': '', 'searchable': True, 'orderable': True,
             'search': {'value': '', 'regex': False}}
        ]
        query_params = {
            'order': json.dumps({'column': 0, 'dir': 'desc'})
        }

        query_mock = self._get_query_mock()
        with patch('bg_utils.mongo.models.Request.objects', return_value=query_mock):
            self.app.get('/api/v1/requests?' +
                         self._datatables_query(columns=columns, query_params=query_params))

            query_mock.order_by.assert_called_once_with(
                '-' + order_column_name)

    @patch('bg_utils.parser.BeerGardenParser.parse_request_dict', Mock(side_effect=ValueError))
    def test_post_parse_failure(self):
        rv = self.app.post('/api/v1/requests', None)
        self.assertEqual(rv.status_code, 400)

    @patch('bg_utils.parser.BeerGardenParser.parse_request_dict')
    def test_post_invalid_message(self, parse_mock):
        brew_view.backend.validateRequest.return_value = Mock(valid=False, message="message")
        mock_request = Mock(id='id')
        mock_request.parent = None
        parse_mock.return_value = mock_request

        rv = self.app.post('/api/v1/requests', {})
        self.assertEqual(parse_mock.call_count, 1)
        self.assertEqual(mock_request.save.call_count, 1)
        self.assertEqual(brew_view.transport.open.call_count, 1)
        self.assertEqual(brew_view.backend.validateRequest.call_count, 1)
        brew_view.backend.validateRequest.assert_called_with('id')
        self.assertEqual(mock_request.delete.call_count, 1)
        self.assertEqual(rv.status_code, 400)

    @patch('bg_utils.parser.BeerGardenParser.parse_request_dict')
    @patch('brew_view.controllers.request_list_api.url_for', Mock(return_value='some_url'))
    def test_post_valid_request(self, parse_mock):
        brew_view.backend.validateRequest.return_value = Mock(valid=True, message="message")
        mock_request = Mock(id='id')
        mock_request.parent = None
        parse_mock.return_value = mock_request

        rv = self.app.post('/api/v1/requests', {})
        self.assertEqual(parse_mock.call_count, 1)
        self.assertEqual(mock_request.save.call_count, 1)
        self.assertEqual(brew_view.transport.open.call_count, 1)
        self.assertEqual(brew_view.backend.validateRequest.call_count, 1)
        self.assertEqual(brew_view.backend.processRequest.call_count, 1)
        brew_view.backend.validateRequest.assert_called_with('id')
        brew_view.backend.processRequest.assert_called_with('id')
        self.assertEqual(brew_view.transport.close.call_count, 1)
        self.assertEqual(rv.status_code, 202)
        self.assertEqual(rv.headers.has_key('Location'), True)

    @patch('bg_utils.parser.BeerGardenParser.parse_request_dict')
    @patch('brew_view.controllers.request_list_api.url_for', Mock(return_value='some_url'))
    @patch('bg_utils.mongo.models.request.Request.objects')
    def test_post_request_with_parent(self, object_mock, parse_mock):
        brew_view.backend.validateRequest.return_value = Mock(valid=True, message="message")
        mock_request = Mock(id='id')
        mock_request.parent = 'parent_id'
        parse_mock.return_value = mock_request

        parent_mock = Mock(name='ParentMock')
        object_mock.get.return_value = parent_mock

        self.app.post('/api/v1/requests', {})
        self.assertIs(mock_request.parent, parent_mock)
