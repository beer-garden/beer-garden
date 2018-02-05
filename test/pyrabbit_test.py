import unittest

from mock import Mock, patch
from pyrabbit2.http import HTTPError, NetworkError

from bartender.pyrabbit import PyrabbitClient


class PyrabbitClientTest(unittest.TestCase):

    def setUp(self):
        self.client_mock = Mock(name='client_mock')

        self.host = 'localhost'
        self.port = 15672
        self.user = 'user'
        self.password = 'password'
        self.virtual_host = '/'

        self.client = PyrabbitClient(host=self.host, port=self.port, user=self.user, password=self.password)
        self.client._client = self.client_mock

    def test_is_alive(self):
        self.client_mock.is_alive.return_value = True
        self.assertTrue(self.client.is_alive())

    def test_not_alive(self):
        self.client_mock.is_alive.side_effect = NetworkError
        self.assertFalse(self.client.is_alive())

    def test_verify_virtual_host(self):
        virtual_host_mock = Mock()
        self.client_mock.get_vhost.return_value = virtual_host_mock

        self.assertEqual(virtual_host_mock, self.client.verify_virtual_host())
        self.client_mock.get_vhost.assert_called_once_with(self.client._virtual_host)

    def test_verify_virtual_host_exception(self):
        self.client_mock.get_vhost.side_effect = ValueError

        self.assertRaises(ValueError, self.client.verify_virtual_host)
        self.client_mock.get_vhost.assert_called_once_with(self.client._virtual_host)

    def test_get_queue_size_good(self):
        self.client_mock.get_queue.return_value = {'messages': 1}

        self.assertEqual(1, self.client.get_queue_size('queue'))
        self.assertEqual(self.client_mock.get_queue.call_count, 1)
        self.client_mock.get_queue.assert_called_with('/', 'queue')

    def test_get_queue_idle(self):
        self.client_mock.get_queue.return_value = {}

        self.assertEqual(0, self.client.get_queue_size('queue'))
        self.assertEqual(self.client_mock.get_queue.call_count, 1)
        self.client_mock.get_queue.assert_called_with('/', 'queue')

    def test_get_queue_size_no_queue(self):
        self.client_mock.get_queue.side_effect = HTTPError({}, status=404, reason='something')
        self.assertRaises(HTTPError, self.client.get_queue_size, 'queue')

    def test_get_queue_size_bad_exception(self):
        self.client_mock.get_queue.side_effect = HTTPError({}, status=500, reason='something')
        self.assertRaises(HTTPError, self.client.get_queue_size, 'queue')

    def test_clear_queue_no_messages(self):
        self.client_mock.get_queue.return_value = {'messages_ready': 0}

        self.client.clear_queue('queue')
        self.assertTrue(self.client_mock.get_queue.called)
        self.assertFalse(self.client_mock.get_messages.called)

    def test_clear_queue_idle_queue(self):
        self.client_mock.get_queue.return_value = {}

        self.client.clear_queue('queue')
        self.assertTrue(self.client_mock.get_queue.called)
        self.assertFalse(self.client_mock.get_messages.called)

    @patch('bartender.pyrabbit.BeerGardenSchemaParser')
    def test_clear_queue(self, parser_mock):
        fake_request = Mock(id='id', status='CREATED')
        parser_mock.parse_request.return_value = fake_request
        self.client_mock.get_queue.return_value = {'messages_ready': 1}
        self.client_mock.get_messages.return_value = [{'payload': fake_request}]

        self.client.clear_queue('queue')
        self.assertEqual(fake_request.status, 'CANCELED')
        self.assertTrue(fake_request.save.called)
        parser_mock.parse_request.assert_called_with(fake_request, from_string=True)

    @patch('bartender.pyrabbit.BeerGardenSchemaParser')
    def test_clear_queue_bad_payload(self, parser_mock):
        fake_request = Mock(id='id', status='CREATED')
        parser_mock.parse_request.side_effect = ValueError
        self.client_mock.get_queue.return_value = {'messages_ready': 1}
        self.client_mock.get_messages.return_value = [{'payload': fake_request}]

        self.client.clear_queue('queue')
        self.assertEqual(fake_request.status, 'CREATED')
        self.assertFalse(fake_request.save.called)
        self.assertTrue(self.client_mock.get_messages.called)
        self.client_mock.get_messages.assert_called_with('/', 'queue', count=1, requeue=False)
        parser_mock.parse_request.assert_called_once_with(fake_request, from_string=True)

    @patch('bartender.pyrabbit.BeerGardenSchemaParser')
    def test_clear_queue_race_condition_met(self, parser_mock):
        self.client_mock.get_queue.return_value = {'messages_ready': 1}
        self.client_mock.get_messages.return_value = []

        self.client.clear_queue('queue')
        self.assertTrue(self.client_mock.get_messages.called)
        self.assertFalse(parser_mock.parse_request.called)

    def test_delete_queue(self):
        self.client.delete_queue('queue')
        self.assertTrue(self.client_mock.delete_queue.called)

    def test_destroy_queue_all_exceptions(self):
        disconnect_consumers_mock = Mock(side_effect=ValueError)
        clear_queue_mock = Mock(side_effect=ValueError)
        delete_queue = Mock(side_effect=ValueError)
        self.client.disconnect_consumers = disconnect_consumers_mock
        self.client.clear_queue = clear_queue_mock
        self.client.delete_queue = delete_queue

        self.client.destroy_queue('queue_name', True)
        self.assertTrue(disconnect_consumers_mock.called)
        self.assertTrue(clear_queue_mock.called)
        self.assertTrue(delete_queue.called)

    def test_destroy_queue_with_http_errors(self):
        disconnect_consumers_mock = Mock(side_effect=HTTPError({}, status=500))
        clear_queue_mock = Mock(side_effect=HTTPError({}, status=500))
        delete_queue = Mock(side_effect=HTTPError({}, status=500))
        self.client.disconnect_consumers = disconnect_consumers_mock
        self.client.clear_queue = clear_queue_mock
        self.client.delete_queue = delete_queue

        self.client.destroy_queue('queue_name', True)
        self.assertTrue(disconnect_consumers_mock.called)
        self.assertTrue(clear_queue_mock.called)
        self.assertTrue(delete_queue.called)

    def test_destroy_queue_no_errors(self):
        disconnect_consumers_mock = Mock()
        clear_queue_mock = Mock()
        delete_queue = Mock()
        self.client.disconnect_consumers = disconnect_consumers_mock
        self.client.clear_queue = clear_queue_mock
        self.client.delete_queue = delete_queue

        self.client.destroy_queue('queue_name', True)
        self.assertTrue(disconnect_consumers_mock.called)
        self.assertTrue(clear_queue_mock.called)
        self.assertTrue(delete_queue.called)

    def test_destroy_queue_none_queue_name(self):
        disconnect_consumers_mock = Mock()
        clear_queue_mock = Mock()
        delete_queue = Mock()
        self.client.disconnect_consumers = disconnect_consumers_mock
        self.client.clear_queue = clear_queue_mock
        self.client.delete_queue = delete_queue

        self.client.destroy_queue(None)
        self.assertFalse(disconnect_consumers_mock.called)
        self.assertFalse(clear_queue_mock.called)
        self.assertFalse(delete_queue.called)

    def test_disconnect_consumers(self):
        consumer_details = [{'queue': {'name': 'queue_name'}, 'channel_details': {'connection_name': 'conn'}}]
        self.client_mock.get_channels.return_value = [{'name': 'channel_name'}]
        self.client_mock.get_channel.return_value = {'consumer_details': consumer_details}

        self.client.disconnect_consumers('queue_name')
        self.client_mock.delete_connection.assert_called_once_with('conn')

    def test_disconnect_consumers_no_channels(self):
        self.client_mock.get_channels.return_value = None

        self.client.disconnect_consumers('queue_name')
        self.assertFalse(self.client_mock.delete_connection.called)

    def test_disconnect_consumers_no_channel(self):
        channel = {'name': 'channel_name'}
        self.client_mock.get_channels.return_value = [channel]
        self.client_mock.get_channel.return_value = None

        self.client.disconnect_consumers('queue_name')
        self.assertFalse(self.client_mock.delete_connection.called)
