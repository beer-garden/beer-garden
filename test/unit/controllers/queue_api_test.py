from mock import MagicMock, Mock, patch

from . import TestHandlerBase


class QueueAPITest(TestHandlerBase):

    def setUp(self):
        self.client_mock = Mock(name='client_mock')
        self.fake_context = MagicMock(__enter__=Mock(return_value=self.client_mock), __exit__=Mock(return_value=False))

        super(QueueAPITest, self).setUp()

    @patch('brew_view.controllers.queue_api.thrift_context')
    def test_delete_calls(self, context_mock):
        context_mock.return_value = self.fake_context

        self.fetch('/api/v1/admin/queues/name', method='DELETE')
        self.client_mock.clearQueue.assert_called_once_with('name')
