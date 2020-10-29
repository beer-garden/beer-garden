import stomp
import logging
import time
from brewtils.schema_parser import SchemaParser
import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.processors import append_headers, process_send_message

logger = logging.getLogger(__name__)


def send_message(message=None, headers=None, conn=None, send_destination=None):
    if headers is None:
        headers = {}
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
                destination=send_destination,
            )


def send_error_msg(error_msg=None, headers=None, conn=None, send_destination=None):
    if headers is None:
        headers = {}

    error_headers = None
    error_headers = append_headers(error_headers, headers)

    if conn.is_connected():
        if "reply-to" in headers:
            conn.send(
                body=error_msg,
                headers=error_headers,
                destination=headers["reply-to"],
            )
        else:
            conn.send(
                body=error_msg,
                headers=error_headers,
                destination=send_destination,
            )
    pass


class OperationListener(stomp.ConnectionListener):
    def __init__(self, conn=None, send_destination=None):
        self.conn = conn
        self.send_destination = send_destination

    def on_error(self, headers, message):
        logger.warning("received an error:" + str(headers))

    def on_message(self, headers, message):
        try:
            operation = SchemaParser.parse_operation(message, from_string=True)
            if hasattr(operation, "kwargs"):
                operation.kwargs.pop("wait_timeout", None)
            result = beer_garden.router.route(operation)
            send_message(
                message=result,
                headers=headers,
                conn=self.conn,
                send_destination=self.send_destination,
            )
        except Exception as e:
            send_error_msg(
                error_msg=str(e),
                headers=headers,
                conn=self.conn,
                send_destination=self.send_destination,
            )
            logger.warning(str(e))


class Connection:
    def __init__(
        self,
        host_and_ports=None,
        send_destination=None,
        subscribe_destination=None,
        ssl=None,
        username=None,
        password=None,
    ):
        self.username = username
        self.password = password
        self.subscribe_destination = subscribe_destination
        self.send_destination = send_destination
        self.bg_active = True
        self.conn = stomp.Connection(
            host_and_ports=host_and_ports, heartbeats=(10000, 0)
        )
        if ssl:
            if ssl.use_ssl:
                self.conn.set_ssl(
                    for_hosts=host_and_ports,
                    key_file=ssl.private_key,
                    cert_file=ssl.cert_file,
                )
        if send_destination:
            self.conn.set_listener("", OperationListener(self.conn, send_destination))

    def connect(self, connected_message=None):
        wait_time = 0.1
        while not self.conn.is_connected() and self.bg_active:
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
                            "durable-subscription-name": "operations",
                        },
                    )
                if connected_message is not None and self.conn.is_connected():
                    logger.info("Stomp successfully " + connected_message)

            except Exception as e:
                logger.warning(str(e))
                logger.warning("Waiting %.1f seconds before next attempt", wait_time)
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, 30)

    def disconnect(self):
        self.bg_active = False
        if self.conn.is_connected():
            self.conn.disconnect()

    def is_connected(self):
        return self.conn.is_connected()

    def send_event(self, event):
        send_message(
            message=event, conn=self.conn, send_destination=self.send_destination
        )
