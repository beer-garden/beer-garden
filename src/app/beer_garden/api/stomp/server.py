import sys
import stomp
import logging
import time
import beer_garden.config as config
from brewtils.models import Event, Events, Request, Operation, System
from brewtils.schema_parser import SchemaParser
import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.processors import append_headers, process_send_message


conn = None
bg_active = False


def send_message(message, headers={}):
    global conn
    stomp_config = config.get("entry.stomp")
    message, response_headers = process_send_message(message)
    response_headers = append_headers(
        response_headers=response_headers, request_headers=headers
    )
    if conn.is_connected():
        if "reply-to" in headers:
            conn.send(
                body=message, headers=response_headers, destination=headers["reply-to"]
            )
        else:
            conn.send(
                body=message,
                headers=response_headers,
                destination=stomp_config.event_destination,
            )


def send_error_msg(error, headers):
    global conn
    stomp_config = config.get("entry.stomp")
    error_headers = None
    error_headers = append_headers(error_headers, headers)

    if conn.is_connected():
        if "reply-to" in headers:
            conn.send(
                body=error.__str__(),
                headers=error_headers,
                destination=headers["reply-to"],
            )
        else:
            conn.send(
                body=error.__str__(),
                headers=error_headers,
                destination=stomp_config.event_destination,
            )
    pass


class OperationListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print("received an error:", headers)

    def on_message(self, headers, message):
        error = None
        error_msg = None
        operation = None
        try:
            operation = SchemaParser.parse_operation(message, from_string=True)
            if hasattr(operation, "kwargs"):
                operation.kwargs.pop("wait_timeout", None)
        except:
            error_msg = "Failed to parse message"
            error = sys.exc_info()

        result = None
        if error_msg is None:
            try:
                result = beer_garden.router.route(operation)
            except:
                error_msg = "Failed to route operation"
                error = sys.exc_info()
        if error is not None:
            send_error_msg(error, headers)
        if result is not None:
            send_message(result, headers)


class Connection:
    @staticmethod
    def __init__():
        global bg_active, conn
        stomp_config = config.get("entry.stomp")
        host_and_ports = [(stomp_config.host, stomp_config.port)]
        bg_active = True
        conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))
        if stomp_config.use_ssl:
            conn.set_ssl(
                for_hosts=host_and_ports,
                key_file=stomp_config.private_key,
                cert_file=stomp_config.cert_file,
            )
        conn.set_listener("", OperationListener())

    @staticmethod
    def connect(connected_message=None):
        global conn
        stomp_config = config.get("entry.stomp")
        logger = logging.getLogger(__name__)
        wait_time = 0.1
        while not conn.is_connected():
            try:
                conn.connect(
                    username=stomp_config.username,
                    passcode=stomp_config.password,
                    wait=True,
                    headers={"client-id": stomp_config.username},
                )
                conn.subscribe(
                    destination=stomp_config.operation_destination,
                    id=stomp_config.username,
                    ack="auto",
                    headers={
                        "subscription-type": "MULTICAST",
                        "durable-subscription-name": "operations",
                    },
                )
                if connected_message is not None and conn.is_connected():
                    logger.info("Stomp successfully " + connected_message)

            except:
                logger.warning("Failed to make stomp connection")
                logger.warning("Waiting %.1f seconds before next attempt", wait_time)
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, 30)

    @staticmethod
    def disconnect():
        global bg_active, conn
        bg_active = False
        if conn.is_connected():
            conn.disconnect()

    @staticmethod
    def is_connected():
        global conn
        return conn.is_connected()

    @staticmethod
    def send_event(event):
        send_message(event)
