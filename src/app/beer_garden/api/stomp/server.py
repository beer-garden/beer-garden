import stomp
from brewtils.models import Event, Events, Request, Operation, System
from brewtils.schema_parser import SchemaParser
import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.processors import append_headers, process_event_message

conn = None


class OperationListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error:', headers)

    def on_message(self, headers, message):
        global conn
        operation = SchemaParser.parse_operation(
            message, from_string=True
        )
        if hasattr(operation, 'kwargs'):
            if 'wait_timeout' in operation.kwargs and operation.operation_type == "REQUEST_CREATE":
                operation.kwargs['wait_timeout'] = 0
        result = beer_garden.router.route(operation)
        if result is not None:
            many = isinstance(result, list)
            model_class = result.__class__.__name__

            if many:
                model_class = result[0].__class__.__name__
            response_headers = {'model_class': model_class, 'many': many}
            response_headers = append_headers(headers=response_headers)
            result = SchemaParser.serialize(result, to_string=True, many=many)
            if 'reply-to' in headers:
                conn.send(body=result, headers=response_headers, destination=headers['reply-to'])
            else:
                conn.send(body=result, headers=response_headers, destination='beergarden/events')


class Connection:
    def __init__(self, hosts=None):
        if hosts is None:
            hosts = [('localhost', 61613)]
        global conn
        conn = stomp.Connection(host_and_ports=hosts, heartbeats=(10000, 0))
        conn.set_listener('', OperationListener())
        conn.connect(username='beer_garden', passcode='password', wait=True, headers={'client-id': 'BeerGarden'})
        conn.subscribe(destination='beergarden/operations', id='beer_garden', ack='auto',
                       headers={'subscription-type': 'MULTICAST', 'durable-subscription-name': 'operations'})

    @staticmethod
    def disconnect():
        global conn
        if conn.is_connected():
            conn.disconnect()

    @staticmethod
    def send(event):
        message = process_event_message(event_message=event)
        response_headers = {'model_class': event.__class__.__name__, 'many': False}
        response_headers = append_headers(headers=response_headers)

        # response_headers["Others"] = Value

        conn.send(body=SchemaParser.serialize(message, to_string=True), headers=response_headers,
                  destination='beergarden/events')
