import unittest

from mock import Mock, patch

from bartender.pika import PikaClient


class PikaClientTest(unittest.TestCase):

    def setUp(self):
        self.publish_mock = Mock()
        self.request_mock = Mock(id='id', command='foo', status=None)

        self.host = 'localhost'
        self.port = 5672
        self.user = 'user'
        self.password = 'password'

        self.client = PikaClient(host=self.host, port=self.port, user=self.user, password=self.password)
        self.client.publish = self.publish_mock

    @patch('bartender.pika.SchemaParser', Mock(serialize_request=Mock(return_value='body')))
    def test_publish_request(self):
        self.client.publish_request(self.request_mock, routing_key='queue_name')
        self.publish_mock.assert_called_with('body', headers={'request_id': 'id'}, routing_key='queue_name')

    @patch('bartender.pika.get_routing_key', Mock(return_value='queue_name_1'))
    @patch('bartender.pika.SchemaParser', Mock(serialize_request=Mock(return_value='body')))
    def test_publish_request_no_routing_key(self):
        self.client.publish_request(self.request_mock)
        self.publish_mock.assert_called_with('body', headers={'request_id': 'id'}, routing_key='queue_name_1')

    @patch('bartender.pika.get_routing_key', Mock(return_value='queue_name_2'))
    @patch('bartender.pika.SchemaParser', Mock(serialize_request=Mock(return_value='body')))
    def test_publish_request_with_expiration(self):
        self.client.publish_request(self.request_mock, expiration=10)
        self.publish_mock.assert_called_with('body', headers={'request_id': 'id'}, routing_key='queue_name_2',
                                             expiration=10)

    @patch('bartender.pika.Request')
    def test_start(self, request_mock):
        publish_request_mock = Mock()
        self.client.publish_request = publish_request_mock

        self.client.start(system='foo', version='1.0.0', instance='default')
        self.assertEqual('_start', request_mock.call_args[1]['command'])
        publish_request_mock.assert_called_once_with(request_mock.return_value, routing_key='admin.foo.1-0-0.default')

    @patch('bartender.pika.Request')
    def test_stop(self, request_mock):
        publish_request_mock = Mock()
        self.client.publish_request = publish_request_mock

        self.client.stop(system='foo', version='1.0.0', instance='default')
        self.assertEqual('_stop', request_mock.call_args[1]['command'])
        publish_request_mock.assert_called_once_with(request_mock.return_value, routing_key='admin.foo.1-0-0.default')
