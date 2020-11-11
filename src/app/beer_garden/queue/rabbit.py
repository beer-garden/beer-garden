# -*- coding: utf-8 -*-
import logging
import random
import string
from typing import List

import pyrabbit2.api
import pyrabbit2.http
from brewtils.errors import NotFoundError
from brewtils.models import Instance, Request, System
from brewtils.pika import TransientPikaClient
from brewtils.schema_parser import SchemaParser

import beer_garden.config as config
import beer_garden.requests

logger = logging.getLogger(__name__)

clients = {}


def check_connection(connection_name: str):
    return clients[connection_name].is_alive()


def create_clients(mq_config):
    global clients

    clients = {
        "pika": TransientPikaClient(
            host=mq_config.host,
            port=mq_config.connections.message.port,
            ssl=mq_config.connections.message.ssl,
            user=mq_config.connections.admin.user,
            password=mq_config.connections.admin.password,
            virtual_host=mq_config.virtual_host,
            connection_attempts=mq_config.connection_attempts,
            blocked_connection_timeout=mq_config.blocked_connection_timeout,
            exchange=mq_config.exchange,
        ),
        "pyrabbit": PyrabbitClient(
            host=mq_config.host,
            virtual_host=mq_config.virtual_host,
            admin_expires=mq_config.admin_queue_expiry,
            **mq_config.connections.admin,
        ),
    }


def initial_setup():
    logger.debug("Verifying message virtual host...")
    clients["pyrabbit"].verify_virtual_host()

    logger.debug("Ensuring admin queue expiration policy...")
    clients["pyrabbit"].ensure_admin_expiry()

    logger.debug("Declaring message exchange...")
    clients["pika"].declare_exchange()


def create(instance: Instance, system: System) -> dict:
    """Create request and admin queues for a given instance

    Args:
        instance: The Instance to create queues for
        system: The System the Instance belongs to

    Returns:
        Dictionary describing the created queues
    """
    routing_words = [system.namespace, system.name, system.version, instance.name]
    request_queue_name = get_routing_key(*routing_words)
    clients["pika"].setup_queue(
        request_queue_name,
        {"durable": True, "arguments": {"x-max-priority": 1}},
        [request_queue_name],
    )

    suffix = [random.choice(string.ascii_lowercase + string.digits) for _ in range(10)]
    routing_words.append("".join(suffix))

    admin_keys = get_routing_keys(*routing_words, is_admin=True)
    admin_queue_name = admin_keys[-1]
    clients["pika"].setup_queue(
        admin_queue_name,
        {"durable": True, "arguments": {"x-max-priority": 1}},
        admin_keys,
    )

    mq_config = config.get("mq")
    plugin_config = config.get("plugin")
    connection = {
        "host": plugin_config.mq.host,
        "port": mq_config.connections.message.port,
        "user": mq_config.connections.message.user,
        "password": mq_config.connections.message.password,
        "virtual_host": mq_config.virtual_host,
        "ssl": {"enabled": mq_config.connections.message.ssl.enabled},
    }

    return {
        "queue_type": "rabbitmq",
        "queue_info": {
            "admin": {"name": admin_queue_name},
            "request": {"name": request_queue_name},
            "connection": connection,
        },
    }


def put(request: Request, headers: dict = None, **kwargs) -> None:
    """Put a Request on a queue

    If a routing_key is specified in the kwargs, it will be used. If not, system and
    instance info on the Request will be used, along with the ``is_admin`` kwarg.

    If the Request has an ID it will be added to the headers as 'request_id'.

    Args:
        request: The Request to publish
        headers: Headers to use when publishing
        **kwargs:
            is_admin: Will be passed to get_routing_key
            Other arguments will be passed to the client publish method

    Returns:
        None
    """
    kwargs["headers"] = headers or {}
    if request.id:
        kwargs["headers"]["request_id"] = request.id

    if "routing_key" not in kwargs:
        kwargs["routing_key"] = get_routing_key(
            request.namespace,
            request.system,
            request.system_version,
            request.instance_name,
            is_admin=kwargs.get("is_admin", False),
        )

    clients["pika"].publish(SchemaParser.serialize_request(request), **kwargs)


def count(queue_name: str) -> int:
    return clients["pyrabbit"].get_queue_size(queue_name)


def clear(queue_name: str) -> None:
    logger.debug("Clearing queue %s", queue_name)
    try:
        clients["pyrabbit"].clear_queue(queue_name)
    except pyrabbit2.http.HTTPError as ex:
        if ex.status == 404:
            raise NotFoundError("No queue named %s" % queue_name)
        else:
            raise


def remove(queue_name: str, **kwargs) -> None:
    clients["pyrabbit"].destroy_queue(queue_name, **kwargs)


class PyrabbitClient(object):
    """Class that implements a connection to RabbitMQ Management HTTP API"""

    def __init__(
        self,
        host="localhost",
        port=15672,
        user="guest",
        password="guest",
        virtual_host="/",
        ssl=None,
        admin_expires=None,
    ):
        self.logger = logging.getLogger(__name__)
        self._admin_expires = admin_expires

        # Pyrabbit won't infer the default virtual host ('/'). So we need to enforce it
        self._virtual_host = virtual_host or "/"

        ssl = ssl or {}
        verify = ssl.get("ca_cert", True) if ssl.get("ca_verify") else False

        # The client for doing Admin things over the HTTP API
        self._client = pyrabbit2.api.Client(
            "%s:%s" % (host, port),
            user,
            password,
            scheme="https" if ssl.get("enabled") else "http",
            verify=verify,
            cert=ssl.get("client_cert"),
        )

    def is_alive(self) -> bool:
        try:
            return self._client.is_alive()
        except pyrabbit2.http.NetworkError:
            return False

    def verify_virtual_host(self) -> None:
        """Ensure the virtual host exists"""
        try:
            return self._client.get_vhost(self._virtual_host)
        except Exception:
            self.logger.error(
                "Error verifying virtual host %s, does it exist?", self._virtual_host
            )
            raise

    def ensure_admin_expiry(self) -> None:
        """Ensure that the admin queue expiration policy exists"""
        try:
            kwargs = {
                "pattern": "^admin.*",
                "definition": {"expires": self._admin_expires},
                "priority": 1,
                "apply-to": "queues",
            }
            self._client.create_policy(self._virtual_host, "admin_expiry", **kwargs)
        except Exception:
            self.logger.error("Error creating admin queue expiration policy")
            raise

    def get_queue_size(self, queue_name: str) -> int:
        """Get the number of messages in a queue.

        Args:
            queue_name: The queue name

        Returns:
            The number of messages in the queue

        Raises:
            pyrabbit2.http.HTTPError: Connection error or queue does not exist
        """
        self.logger.debug("Getting queue Size for: %s", queue_name)
        try:
            return self._client.get_queue(self._virtual_host, queue_name).get(
                "messages", 0
            )
        except pyrabbit2.http.HTTPError as ex:
            if ex.status == 404:
                self.logger.error("Queue '%s' could not be found", queue_name)
            else:
                self.logger.error("Could not connect to queue '%s'", queue_name)
            raise ex

    def clear_queue(self, queue_name: str) -> None:
        """Remove all messages in a queue.

        Args:
            queue_name: The queue name
        """
        self.logger.info("Clearing Queue: %s", queue_name)

        queue_dictionary = self._client.get_queue(self._virtual_host, queue_name)
        number_of_messages = queue_dictionary.get("messages_ready", 0)

        while number_of_messages > 0:
            self.logger.debug("Getting the Next Message")
            messages = self._client.get_messages(
                self._virtual_host, queue_name, count=1, requeue=False
            )
            if messages and len(messages) > 0:
                message = messages[0]
                try:
                    request = SchemaParser.parse_request(
                        message["payload"], from_string=True
                    )
                    beer_garden.requests.cancel_request(request.id)
                except Exception as ex:
                    self.logger.exception(f"Error canceling message: {ex}")
            else:
                self.logger.debug(
                    "Race condition: The while loop thought there were more messages "
                    "to ingest but no more messages could be received."
                )
                break

            number_of_messages -= 1

    def delete_queue(self, queue_name: str) -> None:
        """Actually remove a queue

        Args:
            queue_name: The queue name
        """
        self._client.delete_queue(self._virtual_host, queue_name)

    def destroy_queue(
        self, queue_name: str, force_disconnect: bool = False, clear_queue: bool = True
    ) -> None:
        """Remove all remnants of a queue.

        Ignores exceptions and ensures all aspects of the queue are deleted.

        Args:
            queue_name: The queue name
            force_disconnect: Attempt to forcefully disconnect consumers of this queue
            clear_queue: Clear queue before removing
        """
        if queue_name is None:
            return

        if force_disconnect:
            try:
                self.disconnect_consumers(queue_name)
            except pyrabbit2.http.HTTPError as ex:
                if ex.status != 404:
                    self.logger.exception(ex)
            except Exception as ex:
                self.logger.exception(ex)

        if clear_queue:
            try:
                self.clear_queue(queue_name)
            except pyrabbit2.http.HTTPError as ex:
                if ex.status != 404:
                    self.logger.exception(ex)
            except Exception as ex:
                self.logger.exception(ex)

        try:
            self.delete_queue(queue_name)
        except pyrabbit2.http.HTTPError as ex:
            if ex.status != 404:
                self.logger.exception(ex)
        except Exception as ex:
            self.logger.exception(ex)

    def disconnect_consumers(self, queue_name: str) -> None:
        # If there are no channels, then there is nothing to do
        channels = self._client.get_channels() or []
        for channel in channels:

            # If the channel is already gone, just return an empty response
            channel_details = self._client.get_channel(channel["name"]) or {
                "consumer_details": []
            }

            for consumer_details in channel_details["consumer_details"]:
                if queue_name == consumer_details["queue"]["name"]:
                    self._client.delete_connection(
                        consumer_details["channel_details"]["connection_name"]
                    )


def get_routing_keys(*args, **kwargs) -> List[str]:
    """Get a list of routing keys, ordered from least specific to most specific

    Will return all possible routing keys to get a message to a particular system.

    args is used to specify routing words. The correct order is
       System, Version, Instance, Clone ID

    For instance:

        ['test_system'], is_admin=True:
            ['admin', 'admin.test_system']

        ['test_system', '1.0.0'], is_admin=True:
            ['admin', 'admin.test_system', 'admin.test_system.1-0-0']

        ['test_system', '1.0.0', 'default'], is_admin=True:
            [
                'admin',
                'admin.test_system',
                'admin.test_system.1-0-0',
                'admin.test_system.1-0-0.default',
            ]

        ['test_system', '1.0.0', 'default', 'random_text'], is_admin=True:
            [
                'admin',
                'admin.test_system',
                'admin.test_system.1-0-0',
                'admin.test_system.1-0-0.default',
                'admin.test_system.1-0-0.default.random_text',
            ]

    NOTE: Because RabbitMQ uses '.' as the word delimiter all '.' in routing words will
    be replaced with '-'

    Args:
        List of routing key words to include in the routing keys

    Keyword Args:
        is_admin: Will prepend 'admin' to all generated keys if True

    Returns:
        List of routing keys, ordered from general to specific
    """
    routing_keys = ["admin"] if kwargs.get("is_admin", False) else []

    for arg in (y for y in args if y is not None):
        # Make sure we don't have any extra word delimiters
        new_key = arg.replace(".", "-")

        routing_keys.append(
            routing_keys[-1] + "." + new_key if len(routing_keys) else new_key
        )

    return routing_keys


def get_routing_key(*args, **kwargs):
    """Convenience method for getting the most specific routing key"""
    return get_routing_keys(*args, **kwargs)[-1]
