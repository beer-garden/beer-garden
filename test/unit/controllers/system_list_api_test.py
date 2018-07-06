from mock import Mock, patch

from . import TestHandlerBase


class SystemListAPITest(TestHandlerBase):

    def setUp(self):
        self.system_mock = Mock(name="System Mock")
        self.system_mock.filter.return_value = self.system_mock
        self.system_mock.order_by.return_value = self.system_mock

        mongo_patcher = patch('mongoengine.queryset.manager.QuerySetManager.__get__')
        self.addCleanup(mongo_patcher.stop)
        self.get_mock = mongo_patcher.start()
        self.get_mock.return_value = self.system_mock

        serialize_patcher = patch(
            'brew_view.controllers.system_list_api.BeerGardenSchemaParser.serialize_system'
        )
        self.addCleanup(serialize_patcher.stop)
        self.serialize_mock = serialize_patcher.start()
        self.serialize_mock.return_value = 'serialized_system'

        super(SystemListAPITest, self).setUp()

    def test_get(self):
        response = self.fetch('/api/v1/systems')
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))
        self.assertIn(self.system_mock, self.serialize_mock.call_args[0])

    def test_get_exclude_commands(self):
        response = self.fetch('/api/v1/systems?include_commands=False')
        self.assertEqual(200, response.code)
        self.assertEqual(self.serialize_mock.return_value, response.body.decode('utf-8'))
        self.assertEqual(self.serialize_mock.call_args[1]['exclude'], {'commands'})

    @patch('brew_view.controllers.system_list_api.BeerGardenSchemaParser.serialize_system', Mock())
    def test_get_with_filter_param(self):
        self.fetch('/api/v1/systems?name=bar')
        self.system_mock.filter.assert_called_once_with(name='bar')

    @patch('brew_view.controllers.system_list_api.BeerGardenSchemaParser.serialize_system', Mock())
    def test_get_with_filter_params(self):
        self.fetch('/api/v1/systems?name=bar&version=1.0.0')
        self.system_mock.filter.assert_called_once_with(name='bar', version='1.0.0')

    def test_get_ignore_bad_filter_params(self):
        self.fetch('/api/v1/systems?foo=bar')
        self.system_mock.filter.assert_called_once_with()

    @patch('bg_utils.models.System.find_unique', Mock(return_value=False))
    @patch('brew_view.controllers.system_list_api.SystemListAPI._create_new_system')
    @patch('brew_view.controllers.system_list_api.BeerGardenSchemaParser.parse_system')
    def test_post_new_system(self, parse_mock, create_mock):
        parse_mock.return_value = self.system_mock
        create_mock.return_value = Mock(), 201

        response = self.fetch('/api/v1/systems', method='POST', body='')
        self.assertEqual(201, response.code)
        create_mock.assert_called_once_with(self.system_mock)

    @patch('bg_utils.models.System.find_unique')
    @patch('brew_view.controllers.system_list_api.SystemListAPI._update_existing_system')
    @patch('brew_view.controllers.system_list_api.BeerGardenSchemaParser.parse_system')
    def test_post_existing_system(self, parse_mock, update_mock, find_mock):
        parse_mock.return_value = self.system_mock
        db_system_mock = Mock()
        find_mock.return_value = db_system_mock
        update_mock.return_value = Mock(), 200

        response = self.fetch('/api/v1/systems', method='POST', body='')
        self.assertEqual(200, response.code)
        update_mock.assert_called_once_with(db_system_mock, self.system_mock)
