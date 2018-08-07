import pytest
from mock import ANY, MagicMock, Mock, PropertyMock, call
from pika.exceptions import AMQPError

import bg_utils.pika
from bg_utils.pika import TransientPikaClient, get_routing_key, get_routing_keys

host = 'localhost'
port = 5672
user = 'user'
password = 'password'


class TestTransientPikaClient(object):

    @pytest.fixture
    def do_patching(self, monkeypatch, _connection_mock):
        context_mock = MagicMock(
            name='context mock',
            __enter__=Mock(return_value=_connection_mock),
            __exit__=Mock(return_value=False)
        )

        monkeypatch.setattr(bg_utils.pika, 'BlockingConnection',
                            Mock(name='bc mock', return_value=context_mock))

    @pytest.fixture
    def client(self):
        return TransientPikaClient(host=host, port=port, user=user,
                                   password=password)

    @pytest.fixture
    def _channel_mock(self):
        return Mock(name='channel_mock')

    @pytest.fixture
    def _connection_mock(self, _channel_mock):
        return Mock(name='connection_mock',
                    channel=Mock(return_value=_channel_mock))

    @pytest.fixture
    def connection_mock(self, _connection_mock, do_patching):
        return _connection_mock

    @pytest.fixture
    def channel_mock(self, _channel_mock, do_patching):
        return _channel_mock

    def test_is_alive(self, client, connection_mock):
        connection_mock.is_open = True
        assert client.is_alive() is True

    def test_is_alive_exception(self, client, connection_mock):
        is_open_mock = PropertyMock(side_effect=AMQPError)
        type(connection_mock).is_open = is_open_mock

        assert client.is_alive() is False

    def test_declare_exchange(self, client, channel_mock):
        client.declare_exchange()
        assert channel_mock.exchange_declare.called is True

    def test_setup_queue(self, client, channel_mock):
        queue_name = Mock()
        queue_args = {'test': 'args'}
        routing_keys = ['key1', 'key2']

        assert {'name': queue_name, 'args': queue_args} ==\
            client.setup_queue(queue_name, queue_args, routing_keys)
        channel_mock.queue_declare.assert_called_once_with(queue_name, **queue_args)
        channel_mock.queue_bind.assert_has_calls([
            call(queue_name, ANY, routing_key=routing_keys[0]),
            call(queue_name, ANY, routing_key=routing_keys[1])
        ])

    def test_publish(self, monkeypatch, client, channel_mock):
        props_mock = Mock(return_value={})
        message_mock = Mock(id='id', command='foo', status=None)

        monkeypatch.setattr(bg_utils.pika, 'BasicProperties', props_mock)

        client.publish(message_mock, routing_key='queue_name', expiration=10, mandatory=True)
        props_mock.assert_called_with(app_id='beer-garden', content_type='text/plain',
                                      headers=None, expiration=10)
        channel_mock.basic_publish.assert_called_with(exchange='beer_garden',
                                                      routing_key='queue_name',
                                                      body=message_mock, properties={},
                                                      mandatory=True)

    def test_get_routing_key(self):
        assert 'system.1-0-0.instance' == get_routing_key('system', '1.0.0', 'instance')

    def test_get_routing_keys(self):
        assert ['system', 'system.1-0-0', 'system.1-0-0.instance'] ==\
                         get_routing_keys('system', '1.0.0', 'instance')

    def test_get_routing_keys_admin_basic(self):
        assert ['admin'] == get_routing_keys(is_admin=True)

    def test_get_routing_keys_admin_no_clone_id(self):
        assert ['admin', 'admin.system', 'admin.system.1-0-0',
                'admin.system.1-0-0.instance'] ==\
                         get_routing_keys('system', '1.0.0', 'instance', is_admin=True)

    def test_get_routing_keys_admin_clone_id(self):
        expected = ['admin', 'admin.system', 'admin.system.1-0-0',
                    'admin.system.1-0-0.instance',
                    'admin.system.1-0-0.instance.clone']
        assert expected == get_routing_keys('system', '1.0.0', 'instance', 'clone', is_admin=True)
