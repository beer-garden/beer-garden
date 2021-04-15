import logging
from random import choice
from string import ascii_letters
from typing import Any, Dict, Tuple

import certifi
import stomp
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

import beer_garden.events
import beer_garden.router

logger = logging.getLogger(__name__)


def consolidate_headers(*args) -> dict:
    """Consolidates header dictionaries into one dict

    The args list will be iterated in the order provided, so the combined dictionary
    will contain the value of the *last* dictionary to contain a particular key.

    Args:
        The iterable of header dictionaries to combine

    Returns:

    """
    headers = {}

    for header_dict in args:
        if header_dict:
            headers.update(header_dict)

    return headers


def process(body) -> Tuple[str, dict]:
    """Processes a message body prior to sending

    We always want to send Operations. So if the given message is an Event we'll wrap
    it in an Operation.

    Args:
        body: the message body to process

    Returns:
        Tuple of the serialized message and headers dict

    """
    many = isinstance(body, list)

    if body.__class__.__name__ == "Event":
        body = Operation(operation_type="PUBLISH_EVENT", model=body, model_type="Event")

    model_class = (body[0] if many else body).__class__.__name__

    if not isinstance(body, str):
        body = SchemaParser.serialize(body, to_string=True, many=many)

    return body, {"model_class": model_class, "many": many}


def parse_header_list(headers: str) -> Dict[str, str]:
    """Convert a header list (from config, db) into a header dictionary"""
    tmp_headers = {}
    key_to_key = None
    key_to_value = None

    for header in headers:
        header = eval(header)

        for key in header.keys():
            if "key" in key:
                key_to_key = key
            elif "value" in key:
                key_to_value = key

        tmp_headers[header[key_to_key]] = header[key_to_value]

    return tmp_headers


def send(
    body: Any,
    garden_headers: dict = None,
    conn: stomp.Connection = None,
    send_destination: str = None,
    request_headers: dict = None,
):
    message, model_headers = process(body)

    headers = consolidate_headers(request_headers, model_headers, garden_headers)

    if conn.is_connected() and send_destination:
        destination = send_destination
        if request_headers and "reply-to" in request_headers:
            destination = request_headers["reply-to"]

        conn.send(body=message, headers=headers, destination=destination)


class OperationListener(stomp.ConnectionListener):
    def __init__(self, conn=None, send_destination=None):
        self.conn = conn
        self.send_destination = send_destination

    def on_error(self, headers, message):
        logger.warning(f"Error:\n\tMessage: {message}\n\tHeaders: {headers}")

    def on_message(self, headers: dict, message: str):
        """Handle an incoming message

        Will first verify that the model type (according to the message headers) is an
        Operation. When creating requests on a child garden the initial response will be
        the created Request object, which we want to ignore.

        Will parse the message as an Operation and attempt to route it. If the result of
        the routing is truthy will send a response with the result.

        If routing raised an exception an error response will be sent.

        Args:
            headers: Message header dict
            message: The message body

        Returns:
            None
        """
        logger.debug(f"Message:\n\tMessage: {message}\n\tHeaders: {headers}")

        try:
            if headers.get("model_class") == "Operation":
                operation = SchemaParser.parse_operation(message, from_string=True)

                if hasattr(operation, "kwargs"):
                    operation.kwargs.pop("wait_timeout", None)

                result = beer_garden.router.route(operation)

                if result:
                    send(
                        result,
                        request_headers=headers,
                        conn=self.conn,
                        send_destination=self.send_destination,
                    )
        except Exception as e:
            logger.warning(f"Error parsing and routing message: {e}")
            send(
                str(e),
                request_headers=headers,
                conn=self.conn,
                send_destination=self.send_destination,
            )


class Connection:
    """Stomp connection wrapper

    Args:
        host:
        port:
        send_destination:
        subscribe_destination:
        ssl:
        username:
        password:

    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        send_destination: str = None,
        subscribe_destination: str = None,
        ssl=None,
        username: str = None,
        password: str = None,
        **_,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.subscribe_destination = subscribe_destination
        self.send_destination = send_destination

        self.conn = stomp.Connection(
            host_and_ports=[(self.host, self.port)], heartbeats=(10000, 0)
        )

        if ssl and ssl.get("use_ssl"):
            # It's crazy to me that the default behavior is to NOT VERIFY CERTIFICATES
            ca_certs = ssl.get("ca_cert")
            if not ca_certs:
                ca_certs = certifi.where()

            self.conn.set_ssl(
                for_hosts=[(self.host, self.port)],
                key_file=ssl.get("client_key"),
                cert_file=ssl.get("client_cert"),
                ca_certs=ca_certs,
            )

    def connect(self) -> bool:
        try:
            self.conn.connect(
                username=self.username,
                passcode=self.password,
                wait=True,
                # This is needed if the subscribe to a durable topic
                # headers={"client-id": ?},
            )

            if self.subscribe_destination:
                self.conn.set_listener(
                    "", OperationListener(self.conn, self.send_destination)
                )

                self.conn.subscribe(
                    destination=self.subscribe_destination,
                    id="".join([choice(ascii_letters) for _ in range(10)]),
                    ack="auto",
                    # These are needed if the subscribe to a durable topic
                    # headers={
                    #     "subscription-type": "MULTICAST",
                    #     "durable-subscription-name": self.subscribe_destination,
                    # },
                )

            # This is probably always True at this point, but just to be safe
            return self.conn.is_connected()

        except Exception as ex:
            logger.warning(f"Connection error: {ex}")

            return False

    def disconnect(self):
        if self.conn.is_connected():
            self.conn.disconnect()

    def is_connected(self) -> bool:
        return self.conn.is_connected()

    def send(self, body, headers=None):
        send(
            body,
            conn=self.conn,
            send_destination=self.send_destination,
            garden_headers=headers,
        )
