from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser
from typing import Tuple


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


class EventManager:
    """Will simply push events across the connection to the master process"""

    def __init__(self, conn):
        self._conn = conn

    def put(self, event):
        self._conn.send(event)


def process_send_message(message) -> Tuple[str, dict]:
    """Processes response messages and event messages to send

    We always want to send Operations? So if the given message is an Event we'll wrap
    it in an Operation.

    Args:
        message:

    Returns:
        Tuple of the serialized message and response headers dict

    """
    many = isinstance(message, list)

    if message.__class__.__name__ == "Event":
        message = Operation(
            operation_type="PUBLISH_EVENT", model=message, model_type="Event"
        )

    model_class = (message[0] if many else message).__class__.__name__

    message = SchemaParser.serialize(message, to_string=True, many=many)
    response_headers = {"model_class": model_class, "many": many}

    return message, response_headers
