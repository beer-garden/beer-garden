import logging
import stomp
from brewtils.schema_parser import SchemaParser

import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.processors import consolidate_headers, process_send_message

logger = logging.getLogger(__name__)


def send_message(
    message=None,  # TODO - This is not a string? What is it?
    garden_headers: dict = None,
    conn: stomp.Connection = None,
    send_destination: str = None,
    request_headers: dict = None,
):
    message, response_headers = process_send_message(message)

    headers = consolidate_headers(
        response_headers, request_headers, garden_headers
    )

    if conn.is_connected() and send_destination:
        destination = send_destination
        if request_headers and "reply-to" in request_headers:
            destination = request_headers["reply-to"]

        conn.send(body=message, headers=headers, destination=destination)


def send_error_msg(
    error_msg: str = None,
    request_headers: dict = None,
    conn: stomp.Connection = None,
    send_destination: str = None,
    garden_headers: dict = None,
):
    headers = consolidate_headers(
        request_headers, garden_headers, {"model_class": "error_message"}
    )

    if conn.is_connected():
        destination = send_destination
        if request_headers and "reply-to" in request_headers:
            destination = request_headers["reply-to"]

        conn.send(body=error_msg, headers=headers, destination=destination)


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
                send_message(
                    message=result,
                    request_headers=headers,
                    conn=self.conn,
                    send_destination=self.send_destination,
                )
        except Exception as e:
            send_error_msg(
                error_msg=str(e),
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

    def send_event(self, event=None, headers=None):
        send_message(
            message=event,
            conn=self.conn,
            send_destination=self.send_destination,
            garden_headers=headers,
        )
