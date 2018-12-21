from mock import MagicMock, Mock, patch
from tornado.gen import Future

from . import TestHandlerBase


class AdminAPITest(TestHandlerBase):
    def setUp(self):
        self.client_mock = MagicMock(name="client_mock")
        self.fake_context = MagicMock(
            __enter__=Mock(return_value=self.client_mock),
            __exit__=Mock(return_value=False),
        )
        self.future_mock = Future()

        super(AdminAPITest, self).setUp()

    @patch("brew_view.controllers.admin_api.thrift_context")
    def test_patch(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.rescanSystemDirectory.return_value = self.future_mock
        self.future_mock.set_result(None)

        response = self.fetch(
            "/api/v1/admin/",
            method="PATCH",
            body='{"operations": [{"operation": "rescan"}]}',
            headers={"content-type": "application/json"},
        )
        self.assertEqual(204, response.code)
        self.client_mock.rescanSystemDirectory.assert_called_once_with()

    @patch("brew_view.controllers.admin_api.thrift_context")
    def test_patch_exception(self, context_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.rescanSystemDirectory.return_value = self.future_mock
        self.future_mock.set_exception(ValueError())

        response = self.fetch(
            "/api/v1/admin/",
            method="PATCH",
            body='{"operations": [{"operation": "rescan"}]}',
            headers={"content-type": "application/json"},
        )
        self.assertGreaterEqual(response.code, 500)
        self.client_mock.rescanSystemDirectory.assert_called_once_with()

    def test_patch_bad_operation(self):
        response = self.fetch(
            "/api/v1/admin/",
            method="PATCH",
            body='{"operations": [{"operation": "fake"}]}',
            headers={"content-type": "application/json"},
        )
        self.assertGreaterEqual(response.code, 400)
        self.assertLess(response.code, 500)
