import unittest

from mock import MagicMock, Mock, patch

import brew_view


@unittest.skip('TODO')
class AdminAPITest(unittest.TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     brew_view.load_app(environment="test")

    def setUp(self):
        self.app = brew_view.app.test_client()

        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock), __exit__=Mock(return_value=False))

    @patch('brew_view.controllers.admin_api.thrift_context')
    def test_post_check_calls(self, context_mock):
        context_mock.return_value = self.fake_context
        rv = self.app.post('v1/admin/system')
        self.assertEqual(rv.status_code, 204)
        self.client_mock.rescanSystemDirectory.assert_called_once_with()

    @patch('brew_view.controllers.admin_api.thrift_context')
    def test_post_exception(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.rescanSystemDirectory = Mock(side_effect=Exception)
        rv = self.app.post('v1/admin/system')
        self.assertEqual(rv.status_code, 500)
        self.client_mock.rescanSystemDirectory.assert_called_once_with()
