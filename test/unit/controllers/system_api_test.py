import json

import pytest
from mock import MagicMock, Mock, patch
from mongoengine.errors import DoesNotExist
from tornado.gen import Future
from tornado.httpclient import HTTPRequest

from bg_utils.mongo.models import System
from brewtils.models import PatchOperation
from brewtils.schema_parser import SchemaParser
from brewtils.test.utils.comparable import assert_command_equal
from . import TestHandlerBase


@pytest.fixture(autouse=True)
def drop_systems(app):
    System.drop_collection()


class TestSystemAPI(object):

    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, system_dict, mongo_system, system_id):
        mongo_system.deep_save()

        response = yield http_client.fetch(base_url + '/api/v1/systems/' + system_id)
        assert 200 == response.code
        assert system_dict == json.loads(response.body)

    @pytest.mark.gen_test
    def test_get_404(self, http_client, base_url, system_id):
        response = yield http_client.fetch(
            base_url + '/api/v1/systems/' + system_id,
            raise_error=False,
        )
        assert 404 == response.code

    @pytest.mark.gen_test
    @pytest.mark.parametrize('field,value,dev,succeed', [
        # No changes
        (None, None, True, True),
        (None, None, False, True),

        # Name change
        ('name', 'new', True, True),
        ('name', 'new', False, False),
    ])
    def test_patch_commands(
        self, http_client, base_url, mongo_system, system_id, bg_command,
        field, value, dev, succeed,
    ):
        if dev:
            mongo_system.version += '.dev'
        mongo_system.deep_save()

        # Make changes to the new command
        if field:
            setattr(bg_command, field, value)

        # Also delete the id, otherwise mongo gets really confused
        delattr(bg_command, 'id')

        body = PatchOperation(
            operation='replace',
            path='/commands',
            value=SchemaParser.serialize_command(
                [bg_command], to_string=False, many=True
            ),
        )

        request = HTTPRequest(
            base_url + '/api/v1/systems/' + system_id,
            method='PATCH',
            headers={'content-type': 'application/json'},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        if succeed:
            assert 200 == response.code

            updated = SchemaParser.parse_system(
                response.body.decode(), from_string=True
            )
            assert_command_equal(bg_command, updated.commands[0])
        else:
            assert 400 == response.code


class SystemAPITest(TestHandlerBase):

    def setUp(self):
        self.system_mock = Mock(version='1.0', commands=[])

        mongo_patcher = patch('mongoengine.queryset.manager.QuerySetManager.__get__')
        self.addCleanup(mongo_patcher.stop)
        self.get_mock = mongo_patcher.start()
        self.get_mock.return_value.get.return_value = self.system_mock

        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock),
                                      __exit__=Mock(return_value=False))
        self.future_mock = Future()

        super(SystemAPITest, self).setUp()

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_get_system(self, serialize_mock):
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id')
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_system', response.body.decode('utf-8'))

    @patch('brew_view.controllers.system_api.thrift_context')
    def test_delete_system(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.removeSystem.return_value = self.future_mock
        self.future_mock.set_result(None)

        response = self.fetch('/api/v1/systems/id', method='DELETE')
        self.assertEqual(204, response.code)
        self.client_mock.removeSystem.assert_called_once_with('id')

    @patch('brew_view.controllers.system_api.thrift_context')
    def test_delete_system_thrift_exception(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.removeSystem.return_value = self.future_mock
        self.future_mock.set_exception(ValueError())

        response = self.fetch('/api/v1/systems/id', method='DELETE')
        self.assertNotEqual(204, response.code)
        self.client_mock.removeSystem.assert_called_once_with('id')

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.parse_command', Mock())
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_replace_commands_ok(self, serialize_mock):
        body = json.dumps({"operations": [{"operation": "replace", "path": "/commands",
                                           "value": "output"}]})
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_system', response.body.decode('utf-8'))
        self.assertTrue(self.system_mock.upsert_commands.called)

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.parse_command', Mock())
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_replace_commands_bad(self, serialize_mock):
        self.system_mock.commands = ['a command']
        body = json.dumps({"operations": [{"operation": "replace", "path": "/commands",
                                           "value": "output"}]})
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(400, response.code)
        self.assertFalse(self.system_mock.upsert_commands.called)

    @patch('brew_view.controllers.system_api.thrift_context')
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_reload(self, serialize_mock, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.reloadSystem.return_value = self.future_mock
        self.future_mock.set_result(None)
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH',
                              body='{"operations": [{"operation": "reload"}]}',
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_system', response.body.decode('utf-8'))
        self.client_mock.reloadSystem.assert_called_once_with('id')

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.parse_command', Mock())
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_update_metadata(self, serialize_mock):
        self.system_mock.metadata = {"foo": "baz"}
        body = json.dumps({"operations": [{"operation": "update", "path": "/metadata",
                                           "value": {"foo": "bar"}}]})
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_system', response.body.decode('utf-8'))
        self.assertEqual(self.system_mock.metadata, {"foo": "bar"})

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.parse_command', Mock())
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_replace_description(self, serialize_mock):
        self.system_mock.description = "old_description"
        body = json.dumps({"operations": [{"operation": "replace", "path": "/description",
                                           "value": "new_description"}]})
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_system', response.body.decode('utf-8'))
        self.assertEqual(self.system_mock.description, "new_description")

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.parse_command', Mock())
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_replace_null_empty_string(self, serialize_mock):
        self.system_mock.description = "old_description"
        body = json.dumps({"operations": [{"operation": "replace", "path": "/description",
                                           "value": None}]})
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(200, response.code)
        self.assertEqual('serialized_system', response.body.decode('utf-8'))
        self.assertEqual(self.system_mock.description, "")

    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.parse_command', Mock())
    @patch('brew_view.controllers.system_api.BeerGardenSchemaParser.serialize_system')
    def test_patch_invalid_path_for_update(self, serialize_mock):
        body = json.dumps({"operations": [{"operation": "update", "path": "/INVALID",
                                           "value": "doesnt_matter"}]})
        serialize_mock.return_value = 'serialized_system'

        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertEqual(400, response.code)

    def test_patch_no_system(self):
        self.get_mock.return_value.get.side_effect = DoesNotExist

        response = self.fetch('/api/v1/systems/id', method='PATCH',
                              body='{"operations": [{"operation": "fake"}]}',
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)

    def test_patch_replace_bad_path(self):
        body = json.dumps({"operations": [{"operation": "replace",
                                           "path": "/bad", "value": "error"}]})
        response = self.fetch('/api/v1/systems/id', method='PATCH', body=body,
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)

    def test_patch_bad_operation(self):
        response = self.fetch('/api/v1/systems/id', method='PATCH',
                              body='{"operations": [{"operation": "fake"}]}',
                              headers={'content-type': 'application/json'})
        self.assertGreaterEqual(response.code, 400)
