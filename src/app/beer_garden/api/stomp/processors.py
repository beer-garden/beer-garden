from brewtils.models import Event, Events, Request, Operation, System
from brewtils.schema_parser import SchemaParser


# Modify to inject custom headers
def append_headers(response_headers, request_headers=None):
    return response_headers


# Processes response messages and event messages to send
def process_send_message(message):
    many = isinstance(message, list)
    model_class = message.__class__.__name__
    if many:
        model_class = message[0].__class__.__name__
    message = SchemaParser.serialize(message, to_string=True, many=many)
    response_headers = {'model_class': model_class, 'many': many}
    return message, response_headers
