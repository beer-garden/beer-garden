import json

from tornado.gen import Future
from mock import MagicMock, Mock, patch

from brew_view._version import __version__
from . import TestHandlerBase


class ConfigHandlerTest(TestHandlerBase):

    def test_config(self):
        import brew_view
        brew_view.config['application_name'] = 'Rock Garden'

        response = self.fetch('/config')
        self.assertEqual('Rock Garden',
                         json.loads(response.body.decode('utf-8'))['application_name'])


class VersionHandlerTest(TestHandlerBase):

    def setUp(self):
        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock),
                                      __exit__=Mock(return_value=False))
        self.future_mock = Future()

        super(VersionHandlerTest, self).setUp()

    @patch('brew_view.controllers.misc_controllers.thrift_context')
    def test_version_everything_works(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.getVersion.return_value = self.future_mock
        self.future_mock.set_result("bartender_version")

        response = self.fetch('/version')
        output = json.loads(response.body.decode("utf-8"))
        self.client_mock.getVersion.assert_called_once_with()
        self.assertEqual(output, {
            'brew_view_version': __version__,
            'bartender_version': 'bartender_version',
            'current_api_version': 'v1',
            'supported_api_versions': ['v1']
        })

    @patch('brew_view.controllers.misc_controllers.thrift_context')
    def test_version_fail_to_get_backend_version(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.getVersion.return_value = self.future_mock
        self.future_mock.set_exception(ValueError('ERROR'))

        response = self.fetch('/version')
        output = json.loads(response.body.decode("utf-8"))
        self.client_mock.getVersion.assert_called_once_with()
        self.assertEqual(output, {
            'brew_view_version': __version__,
            'bartender_version': 'unknown',
            'current_api_version': 'v1',
            'supported_api_versions': ['v1']
        })
