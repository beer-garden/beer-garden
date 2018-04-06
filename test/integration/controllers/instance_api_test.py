import unittest

from mock import MagicMock, Mock, patch

import brew_view
from brewtils.models import Command, Instance, System
from brewtils.schema_parser import SchemaParser


@unittest.skip('TODO')
class InstanceAPITest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # brew_view.load_app(environment="test")

        cls.parser = SchemaParser()

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.default_instance = Instance(name='default', status='RUNNING')
        self.default_command = Command(id='54ac18f778c4b57e963f3c18', name='command', description='foo')
        self.default_system = System(id='54ac18f778c4b57e963f3c18', name='default_system', version='1.0.0',
                                     instances=[self.default_instance], commands=[self.default_command])

        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock), __exit__=Mock(return_value=False))

    @patch('mongoengine.queryset.QuerySet.get', Mock())
    @patch('brew_view.transport', Mock())
    @patch('brew_view.backend')
    def test_patch_start(self, backend_mock):
        self.app.patch('/api/v1/systems/id', content_type='application/json',
                       data='{"operations": [{"operation": "replace", "path": "/status", "value": "RUNNING"}]}')

        self.assertEqual(1, backend_mock.startSystem.call_count)
        self.assertEqual(0, backend_mock.stopSystem.call_count)

    @patch('mongoengine.queryset.QuerySet.get', Mock())
    @patch('brew_view.transport', Mock())
    @patch('brew_view.backend')
    def test_patch_stop(self, backend_mock):
        self.app.patch('/api/v1/systems/id', content_type='application/json',
                       data='{"operations": [{"operation": "replace", "path": "/status", "value": "STOPPED"}]}')

        self.assertEqual(1, backend_mock.stopSystem.call_count)
        self.assertEqual(0, backend_mock.startSystem.call_count)