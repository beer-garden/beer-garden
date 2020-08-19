import sys
import stomp
import logging
import time
from brewtils.models import Event, Events, Request, Operation, System
from brewtils.schema_parser import SchemaParser
import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.processors import append_headers, process_send_message

conn = None
bg_active = False
username = None
passcode = None


def send_response(result, headers):
    global conn
    message, response_headers = process_send_message(result)
    response_headers = append_headers(response_headers=response_headers, request_headers=headers)
    if conn.is_connected():
        if 'reply-to' in headers:
            conn.send(body=message, headers=response_headers, destination=headers['reply-to'])
        else:
            conn.send(body=message, headers=response_headers, destination='beergarden/events')


def send_error_msg(error, headers):
    global conn
    error_headers = None
    error_headers = append_headers(error_headers, headers)

    if conn.is_connected():
        if 'reply-to' in headers:
            conn.send(body=error.__str__(), headers=error_headers, destination=headers['reply-to'])
        else:
            conn.send(body=error.__str__(), headers=error_headers, destination='beergarden/events')
    pass


class OperationListener(stomp.ConnectionListener):

    def on_error(self, headers, message):
        print('received an error:', headers)

    def on_message(self, headers, message):
        error = None
        error_msg = None
        operation = None
        try:
            operation = SchemaParser.parse_operation(message, from_string=True)
            if hasattr(operation, 'kwargs'):
                if 'wait_timeout' in operation.kwargs and operation.operation_type == "REQUEST_CREATE":
                    operation.kwargs['wait_timeout'] = 0
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
            send_response(result, headers)


class Connection:

    @staticmethod
    def __init__(host_and_ports=None, user_name="beer_garden", password="password"):
        if host_and_ports is None:
            host_and_ports = [('localhost', 61613)]
        global bg_active, conn, username, passcode
        bg_active = True
        username = user_name
        passcode = password
        conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))
        conn.set_listener('', OperationListener())

    @staticmethod
    def connect(connected_message=None):
        global conn, username, passcode
        logger = logging.getLogger(__name__)
        wait_time = 0.1
        while not conn.is_connected():
            try:
                conn.connect(username=username, passcode=passcode, wait=True,
                             headers={'client-id': 'BeerGarden'})
                conn.subscribe(destination='beergarden/operations', id='beer_garden', ack='auto',
                               headers={'subscription-type': 'MULTICAST',
                                        'durable-subscription-name': 'operations'})
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
        global conn, bg_active
        message, response_headers = process_send_message(message=event)
        response_headers = append_headers(response_headers=response_headers)

        # response_headers["Others"] = Value
        if message is not None and conn.is_connected():
            conn.send(body=message, headers=response_headers, destination='beergarden/events')

    @staticmethod
    def send_response(result, headers):
        send_response(result, headers)
