from brewtils.schema_parser import SchemaParser


# Modify to inject custom headers
def append_headers(response_headers, request_headers=None):
    return response_headers


class EventManager:
    """Will simply push events across the connection to the master process"""

    def __init__(self, conn):
        self._conn = conn

    def put(self, event):
        self._conn.send(event)


# Processes response messages and event messages to send
def process_send_message(message):
    many = isinstance(message, list)
    model_class = message.__class__.__name__
    if many:
        model_class = message[0].__class__.__name__
    message = SchemaParser.serialize(message, to_string=True, many=many)
    response_headers = {"model_class": model_class, "many": many}
    return message, response_headers
