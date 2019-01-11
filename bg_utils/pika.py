from __future__ import absolute_import

import logging

from pika import BasicProperties
from pika import BlockingConnection
from pika.exceptions import AMQPError

from brewtils.queues import PikaClient


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
    routing_keys = ["admin"] if kwargs.get("is_admin", False) else []

    for arg in (y for y in args if y is not None):
        # Make sure we don't have any extra word delimiters
        new_key = arg.replace(".", "-")

        routing_keys.append(
            routing_keys[-1] + "." + new_key if len(routing_keys) else new_key
        )

    return routing_keys


class TransientPikaClient(PikaClient):
    """Pika client implementation that creates a new connection and channel for each action"""

    def __init__(self, **kwargs):
        super(TransientPikaClient, self).__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    def is_alive(self):
        try:
            with BlockingConnection(
                self.connection_parameters(connection_attempts=1)
            ) as conn:
                return conn.is_open
        except AMQPError:
            return False

    def declare_exchange(self):
        with BlockingConnection(self._conn_params) as conn:
            conn.channel().exchange_declare(
                exchange=self._exchange, exchange_type="topic", durable=True
            )

    def setup_queue(self, queue_name, queue_args, routing_keys):
        """Will create a new queue with the given args and bind it to the given routing keys"""

        with BlockingConnection(self._conn_params) as conn:
            conn.channel().queue_declare(queue_name, **queue_args)

            for routing_key in routing_keys:
                conn.channel().queue_bind(
                    queue_name, self._exchange, routing_key=routing_key
                )

        return {"name": queue_name, "args": queue_args}

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

            if kwargs.get("confirm"):
                channel.confirm_delivery()

            properties = BasicProperties(
                app_id="beer-garden",
                content_type="text/plain",
                headers=kwargs.get("headers"),
                expiration=kwargs.get("expiration"),
            )

            return channel.basic_publish(
                exchange=self._exchange,
                routing_key=kwargs["routing_key"],
                body=message,
                properties=properties,
                mandatory=kwargs.get("mandatory"),
            )
