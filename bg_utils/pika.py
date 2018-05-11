from __future__ import absolute_import

import logging

from pika import BasicProperties, ConnectionParameters, PlainCredentials
from pika import BlockingConnection
from pika.exceptions import AMQPError


def get_routing_key(*args, **kwargs):
    """Convenience method for getting the most specific routing key"""
    return get_routing_keys(*args, **kwargs)[-1]


def get_routing_keys(*args, **kwargs):
    """Get a list of routing keys for a plugin in order from least specific to most specific.

    Will return all possible routing keys to get a message to a particular system.

    args is used to specify routing words. The correct order is
       System, Version, Instance, Clone ID

    For instance:

        ['test_system'], is_admin=True:
            ['admin', 'admin.test_system']

        ['test_system', '1.0.0'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0']

        ['test_system', '1.0.0', 'default'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0',
                'admin.test_system.1-0-0.default']

        ['test_system', '1.0.0', 'default', 'random_text'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0',
                'admin.test_system.1-0-0.default', 'admin.test_system.1-0-0.default.random_text']

    NOTE: Because RabbitMQ uses '.' as the word delimiter all '.' in routing words will be
        replaced with '-'

    :param args: List of routing key words to include in the routing keys
    :param kwargs: is_admin: Will prepend 'admin' to all generated keys if True
    :return: List of routing keys, ordered from general to specific
    """
    routing_keys = ['admin'] if kwargs.get('is_admin', False) else []

    for arg in (y for y in args if y is not None):
        # Make sure we don't have any extra word delimiters
        new_key = arg.replace('.', '-')

        routing_keys.append(routing_keys[-1] + '.' + new_key if len(routing_keys) else new_key)

    return routing_keys


class ClientBase(object):
    """Base class for connection to RabbitMQ."""

    def __init__(self, host='localhost', port=5672, user='guest', password='guest',
                 connection_attempts=3, heartbeat_interval=3600, virtual_host='/',
                 exchange='beer_garden', ssl_enabled=False):

        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._connection_attempts = connection_attempts
        self._heartbeat_interval = heartbeat_interval
        self._virtual_host = virtual_host
        self._exchange = exchange
        self._ssl_enabled = ssl_enabled

        # Save off the 'normal' connection params so they don't need to be constructed every time
        self._conn_params = self.connection_parameters()

    @property
    def connection_url(self):
        """str: Get the connection URL associated with this client's connection information"""

        return 'amqp%s://%s:%s@%s:%s/%s' % \
               ('s' if self._ssl_enabled else '',
                self._conn_params.credentials.username, self._conn_params.credentials.password,
                self._conn_params.host,
                self._conn_params.port,
                '' if self._conn_params.virtual_host == '/' else self._conn_params.virtual_host)

    def connection_parameters(self, **kwargs):
        """Get ``ConnectionParameters`` associated with this client

        Will construct a ``ConnectionParameters`` object using parameters passed at initialization
        as defaults. Any parameters passed in \*\*kwargs will override initialization parameters.

        Args:
            **kwargs: Overrides for specific parameters

        Returns:
            :obj:`pika.ConnectionParameters`: Generated ConnectionParameters object
        """
        credentials = PlainCredentials(username=kwargs.get('user', self._user),
                                       password=kwargs.get('password', self._password))

        return ConnectionParameters(host=kwargs.get('host', self._host),
                                    port=kwargs.get('port', self._port),
                                    ssl=kwargs.get('ssl_enabled', self._ssl_enabled),
                                    virtual_host=kwargs.get('virtual_host', self._virtual_host),
                                    connection_attempts=kwargs.get('connection_attempts',
                                                                   self._connection_attempts),
                                    heartbeat_interval=kwargs.get('heartbeat_interval',
                                                                  self._heartbeat_interval),
                                    credentials=credentials)


class TransientPikaClient(ClientBase):
    """Pika client implementation that creates a new connection and channel for each action"""

    def __init__(self, **kwargs):
        super(TransientPikaClient, self).__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    def is_alive(self):
        try:
            with BlockingConnection(self.connection_parameters(connection_attempts=1)) as conn:
                return conn.is_open
        except AMQPError:
            return False

    def declare_exchange(self):
        with BlockingConnection(self._conn_params) as conn:
            conn.channel().exchange_declare(exchange=self._exchange,
                                            exchange_type='topic',
                                            durable=True)

    def setup_queue(self, queue_name, queue_args, routing_keys):
        """Will create a new queue with the given args and bind it to the given routing keys"""

        with BlockingConnection(self._conn_params) as conn:
            conn.channel().queue_declare(queue_name, **queue_args)

            for routing_key in routing_keys:
                conn.channel().queue_bind(queue_name, self._exchange, routing_key=routing_key)

        return {
            'name': queue_name,
            'args': queue_args
        }

    def publish(self, message, **kwargs):
        """Publish a message.

        :param message: The message to publish
        :param kwargs: Additional message properties
        :Keyword Arguments:
            * *routing_key* --
              Routing key to use when publishing
            * *headers* --
              Headers to be included as part of the message properties
            * *expiration* --
              Expiration to be included as part of the message properties
            * *confirm* --
              If set to True return False if the message fails to be delivered to the broker
            * *mandatory* --
              If set to True return False if the message can not be routed to any queues
        :return:
            Boolean, behavior depends on setting of the confirm and mandatory flags.
            If both are False then this method will always return True
        """
        with BlockingConnection(self._conn_params) as conn:
            channel = conn.channel()

            if kwargs.get('confirm'):
                channel.confirm_delivery()

            properties = BasicProperties(app_id='beer-garden',
                                         content_type='text/plain',
                                         headers=kwargs.get('headers'),
                                         expiration=kwargs.get('expiration'))

            return channel.basic_publish(exchange=self._exchange,
                                         routing_key=kwargs['routing_key'],
                                         body=message,
                                         properties=properties,
                                         mandatory=kwargs.get('mandatory'))
