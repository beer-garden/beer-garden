import logging
import stomp
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser
from typing import Tuple, Any

import beer_garden.events
import beer_garden.router

logger = logging.getLogger(__name__)


def consolidate_headers(*args) -> dict:
    """Consolidates header dictionaries into one dict

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
        Tuple of the serialized message and response headers dict

    """
    many = isinstance(body, list)

    if body.__class__.__name__ == "Event":
        body = Operation(operation_type="PUBLISH_EVENT", model=body, model_type="Event")

    model_class = (body[0] if many else body).__class__.__name__

    if not isinstance(body, str):
        body = SchemaParser.serialize(body, to_string=True, many=many)

    return body, {"model_class": model_class, "many": many}


def send(
    body: Any,
    garden_headers: dict = None,
    conn: stomp.Connection = None,
    send_destination: str = None,
    request_headers: dict = None,
):
    message, model_headers = process(body)

    headers = consolidate_headers(model_headers, request_headers, garden_headers)

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
        # TODO - Should probably log the message?
        logger.warning("received an error:" + str(headers))

    def on_message(self, headers: dict, message: str):
        """Handle an incoming message

        Will parse the message as an Operation and attempt to route it. If the result of
        the routing is truthy will send a response with the result.

        If routing raised an exception an error response will be sent.

        Args:
            headers: Message header dict
            message: The message body

        Returns:
            None
        """
        try:
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
            send(
                str(e),
                request_headers=headers,
                conn=self.conn,
                send_destination=self.send_destination,
            )
            logger.warning(str(e))


class Connection:
    """Stomp connection wrapper

    Args:
        host_and_ports:
        send_destination:
        subscribe_destination:
        ssl:
        username:
        password:

    """

    def __init__(
        self,
        host_and_ports=None,
        send_destination=None,
        subscribe_destination=None,
        ssl=None,
        username=None,
        password=None,
    ):
        self.host_and_ports = host_and_ports
        self.username = username
        self.password = password
        self.subscribe_destination = subscribe_destination
        self.send_destination = send_destination
        self.bg_active = True
        self.conn = stomp.Connection(
            host_and_ports=host_and_ports, heartbeats=(10000, 0)
        )

        if ssl and ssl.get("use_ssl"):
            self.conn.set_ssl(
                for_hosts=host_and_ports,
                key_file=ssl.get("private_key"),
                cert_file=ssl.get("cert_file"),
            )

        if subscribe_destination:
            self.conn.set_listener("", OperationListener(self.conn, send_destination))

    def connect(self, connected_message=None, wait_time=None, gardens=None):
        if self.host_and_ports:
            if (
                self.host_and_ports[0][0]
                and self.host_and_ports[0][1]
                and self.subscribe_destination
            ):
                try:
                    self.conn.connect(
                        username=self.username,
                        passcode=self.password,
                        wait=True,
                        headers={"client-id": self.username},
                    )
                    if self.subscribe_destination:
                        self.conn.subscribe(
                            destination=self.subscribe_destination,
                            id=self.username,
                            ack="auto",
                            headers={
                                "subscription-type": "MULTICAST",
                                "durable-subscription-name": self.subscribe_destination,
                            },
                        )
                    if connected_message is not None and self.conn.is_connected():
                        logger.info("Stomp successfully " + connected_message)

                except Exception as e:
                    logger.debug(
                        f"Error connecting: {type(e).__name__}. "
                        f"Affected gardens are {[garden.get('name') for garden in gardens]}"
                    )
                    logger.warning(
                        "Waiting %.1f seconds before next attempt", wait_time
                    )

    def disconnect(self):
        self.bg_active = False
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
