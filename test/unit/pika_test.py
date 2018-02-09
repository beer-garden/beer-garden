import unittest

from mock import ANY, MagicMock, Mock, call, patch

from bg_utils.pika import ClientBase, TransientPikaClient, get_routing_key, get_routing_keys


class ClientBaseTest(unittest.TestCase):

    def setUp(self):
        self.host = 'localhost'
        self.port = 5672
        self.user = 'user'
        self.password = 'password'

        self.client = ClientBase(host=self.host, port=self.port, user=self.user,
                                 password=self.password)

    def test_connection_url(self):
        url = self.client.connection_url

        self.assertTrue(url.startswith('amqp://'))
        self.assertIn(self.user, url)
        self.assertIn(self.password, url)
        self.assertIn(self.host, url)
        self.assertIn(str(self.port), url)


class TransientPikaClientTest(unittest.TestCase):

    def setUp(self):
        self.channel_mock = Mock(name='channel_mock')
        self.connection_mock = Mock(name='client_mock',
                                    channel=Mock(return_value=self.channel_mock))

        connection_patcher = patch('bg_utils.pika.BlockingConnection')
        self.addCleanup(connection_patcher.stop)
        connection_patch = connection_patcher.start()
        connection_patch.return_value = MagicMock(
            __enter__=Mock(return_value=self.connection_mock),
            __exit__=Mock(return_value=False))

        self.host = 'localhost'
        self.port = 5672
        self.user = 'user'
        self.password = 'password'

        self.client = TransientPikaClient(host=self.host, port=self.port, user=self.user,
                                          password=self.password)

    def test_declare_exchange(self):
        self.client.declare_exchange()
        self.assertTrue(self.channel_mock.exchange_declare.called)

    def test_setup_queue(self):
        queue_name = Mock()
        queue_args = {'test': 'args'}
        routing_keys = ['key1', 'key2']
        self.assertEqual({'name': queue_name, 'args': queue_args},
                         self.client.setup_queue(queue_name, queue_args, routing_keys))
        self.channel_mock.queue_declare.assert_called_once_with(queue_name, **queue_args)
        self.channel_mock.queue_bind.assert_has_calls([call(queue_name, ANY,
                                                            routing_key=routing_keys[0]),
                                                       call(queue_name, ANY,
                                                            routing_key=routing_keys[1])])

    @patch('bg_utils.pika.BasicProperties')
    def test_publish(self, props_mock):
        props_mock.return_value = {}
        message_mock = Mock(id='id', command='foo', status=None)

        self.client.publish(message_mock, routing_key='queue_name', expiration=10)
        props_mock.assert_called_with(app_id='beer-garden', content_type='text/plain',
                                      headers=None, expiration=10)
        self.channel_mock.basic_publish.assert_called_with(exchange='beer_garden',
                                                           routing_key='queue_name',
                                                           body=message_mock, properties={})

    def test_get_routing_key(self):
        self.assertEqual('system.1-0-0.instance', get_routing_key('system', '1.0.0', 'instance'))

    def test_get_routing_keys(self):
        self.assertEqual(['system', 'system.1-0-0', 'system.1-0-0.instance'],
                         get_routing_keys('system', '1.0.0', 'instance'))

    def test_get_routing_keys_admin_basic(self):
        self.assertEqual(['admin'], get_routing_keys(is_admin=True))

    def test_get_routing_keys_admin_no_clone_id(self):
        self.assertEqual(['admin', 'admin.system', 'admin.system.1-0-0',
                          'admin.system.1-0-0.instance'],
                         get_routing_keys('system', '1.0.0', 'instance', is_admin=True))

    def test_get_routing_keys_admin_clone_id(self):
        self.assertEqual(['admin', 'admin.system', 'admin.system.1-0-0',
                          'admin.system.1-0-0.instance',
                          'admin.system.1-0-0.instance.clone'],
                         get_routing_keys('system', '1.0.0', 'instance', 'clone', is_admin=True))
