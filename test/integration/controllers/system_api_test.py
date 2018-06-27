import unittest

import mongoengine
from mock import MagicMock, Mock, patch

import brew_view
from bg_utils.models import Command, Instance, System
from bg_utils.parser import BeerGardenSchemaParser
from ...utils import TestUtils


@unittest.skip('TODO')
class SystemAPITest(TestUtils, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # brew_view.load_app(environment="test")
        cls.parser = BeerGardenSchemaParser()

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.default_instance = Instance(name='default', status='RUNNING')
        self.default_command = Command(id='54ac18f778c4b57e963f3c18', name='command', description='foo')
        self.default_system = System(id='54ac18f778c4b57e963f3c18', name='default_system', version='1.0.0',
                                     instances=[self.default_instance], commands=[self.default_command],
                                     max_instances='1')

        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock), __exit__=Mock(return_value=False))

    @patch('mongoengine.queryset.QuerySet.get')
    def test_get_system(self, mock_get):
        mock_get.return_value = self.default_system

        response = self.app.get('/api/v1/systems/%s' % self.default_system.id)
        self.assertEqual(200, response.status_code)

        response_system = self.parser.parse_system(response.data, from_string=True)
        self._assert_systems_equal(self.default_system, response_system)

    @patch('mongoengine.queryset.QuerySet.get')
    def test_get_system_no_include_commands(self, mock_get):
        mock_get.return_value = self.default_system

        response = self.app.get('/api/v1/systems/%s?include_commands=false' % self.default_system.id)
        self.assertEqual(200, response.status_code)

        response_system = self.parser.parse_system(response.data, from_string=True)
        self._assert_systems_equal(self.default_system, response_system, include_commands=False)
        self.assertFalse(response_system.commands)

    def test_get_bad_id(self):
        self.assertEqual(400, self.app.get('/api/v1/systems/BADID').status_code)

    @patch('mongoengine.queryset.QuerySet.get', Mock(side_effect=mongoengine.DoesNotExist))
    def test_get_not_found(self):
        self.assertEqual(404, self.app.get('/api/v1/systems/54ac18f778c4b57e963f3c18').status_code)

    @patch('mongoengine.queryset.QuerySet.get')
    def test_delete(self, mock_get):
        mock_system = Mock()
        mock_get.return_value = mock_system

        self.assertEqual(204, self.app.delete('/api/v1/systems/id').status_code)
        mock_system.deep_delete.assert_called_with()

    @patch('bg_utils.models.System.deep_save')
    @patch('mongoengine.queryset.QuerySet.get')
    def test_put(self, get_mock, save_mock):
        get_mock.return_value = self.default_system
        self.default_system.deep_save = Mock()

        response = self.app.put('/api/v1/systems/%s' % self.default_system.id, content_type='application/json',
                                data=self.parser.serialize_system(self.default_system))
        self.assertEqual(200, response.status_code)
        save_mock.assert_called_once_with()

        response_system = self.parser.parse_system(response.data, from_string=True)
        self._assert_systems_equal(self.default_system, response_system)

    @patch('mongoengine.queryset.QuerySet.get', Mock(side_effect=mongoengine.DoesNotExist))
    def test_put_not_found(self):
        self.assertEqual(404, self.app.put('/api/v1/systems/54ac18f778c4b57e963f3c18').status_code)

    @patch('mongoengine.queryset.QuerySet.get')
    def test_put_id_mismatch(self, get_mock):
        get_mock.return_value = self.default_system
        self.default_system.deep_save = Mock()

        response = self.app.put('/api/v1/systems/%s' % self.default_system.id, content_type='application/json',
                                data='{}')
        self.assertEqual(400, response.status_code)

    @patch('mongoengine.queryset.QuerySet.get')
    @patch('brew_view.controllers.system_api.thrift_context')
    def test_patch_reload(self, context_mock, get_mock):
        get_mock.return_value = self.default_system
        context_mock.return_value = self.fake_context
        self.default_system.reload = Mock()

        response = self.app.patch('/api/v1/systems/id', content_type='application/json',
            data='{"operations": [{"operation": "reload", "path": "", "value": ""}]}')
        self.assertEqual(200, response.status_code)
        self.default_system.reload.assert_called_once_with()
        self.client_mock.reloadSystem.assert_called_once_with(str(self.default_system.id))

    @patch('mongoengine.queryset.QuerySet.get', Mock(side_effect=mongoengine.DoesNotExist))
    def test_patch_not_found(self):
        self.assertEqual(404, self.app.patch('/api/v1/systems/54ac18f778c4b57e963f3c18').status_code)

    @patch('mongoengine.queryset.QuerySet.get', Mock())
    @patch('brew_view.controllers.system_api.thrift_context', Mock())
    def test_patch_bad_operation(self):
        response = self.app.patch('/api/v1/systems/id', content_type='application/json',
            data='{"operations": [{"operation": "bad_op", "path": "/status", "value": "STOPPED"}]}')
        self.assertEqual(400, response.status_code)

    @patch('mongoengine.queryset.QuerySet.get', Mock())
    @patch('brew_view.controllers.system_api.thrift_context', Mock())
    def test_patch_bad_path(self):
        response = self.app.patch('/api/v1/systems/id', content_type='application/json',
            data='{"operations": [{"operation": "replace", "path": "bad_path", "value": "STOPPED"}]}')
        self.assertEqual(400, response.status_code)

    @patch('mongoengine.queryset.QuerySet.get', Mock())
    @patch('brew_view.controllers.system_api.thrift_context', Mock())
    def test_patch_bad_value(self):
        response = self.app.patch('/api/v1/systems/id', content_type='application/json',
            data='{"operations": [{"operation": "replace", "path": "/status", "value": "bad_value"}]}')
        self.assertEqual(400, response.status_code)
