# -*- coding: utf-8 -*-
import logging
from typing import Sequence

from brewtils.errors import NotFoundError
from brewtils.models import Instance, Queue, Request
from brewtils.pika import TransientPikaClient
from brewtils.schema_parser import SchemaParser
from pyrabbit2.http import HTTPError

from beer_garden.queue.rabbitmq import get_routing_key, PyrabbitClient

logger = logging.getLogger(__name__)

clients = {}


def create_clients(amq_config):
    global clients
    clients = {
        "pika": TransientPikaClient(
            host=amq_config.host,
            port=amq_config.connections.message.port,
            ssl=amq_config.connections.message.ssl,
            user=amq_config.connections.admin.user,
            password=amq_config.connections.admin.password,
            virtual_host=amq_config.virtual_host,
            connection_attempts=amq_config.connection_attempts,
            blocked_connection_timeout=amq_config.blocked_connection_timeout,
            exchange=amq_config.exchange,
        ),
        "pyrabbit": PyrabbitClient(
            host=amq_config.host,
            virtual_host=amq_config.virtual_host,
            admin_expires=amq_config.admin_queue_expiry,
            **amq_config.connections.admin
        ),
    }


def initial_setup():
    logger.debug("Verifying message virtual host...")
    clients["pyrabbit"].verify_virtual_host()

    logger.debug("Ensuring admin queue expiration policy...")
    clients["pyrabbit"].ensure_admin_expiry()

    logger.debug("Declaring message exchange...")
    clients["pika"].declare_exchange()


def create(name: str, routing_keys: Sequence[str], **kwargs) -> Queue:
    clients["pika"].setup_queue(name, kwargs, routing_keys)

    return Queue(name=name)


def put(request: Request, **kwargs) -> None:
    if "headers" not in kwargs:
        kwargs["headers"] = {}
    if request.id:
        kwargs["headers"]["request_id"] = request.id

    if "routing_key" not in kwargs:
        kwargs["routing_key"] = get_routing_key(
            request.system, request.system_version, request.instance_name
        )

    clients["pika"].publish(SchemaParser.serialize_request(request), **kwargs)


def clear(queue_name: str, instance: Instance = None) -> None:
    logger.debug("Clearing queue %s", queue_name)
    try:
        clients["pyrabbit"].clear_queue(queue_name)
    except HTTPError as ex:
        if ex.status == 404:
            raise NotFoundError("No queue named %s" % queue_name)
        else:
            raise


def remove(queue_name: str, **kwargs) -> None:
    clients["pyrabbit"].destroy_queue(queue_name, **kwargs)
