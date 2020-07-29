from brewtils.models import Event, Events, Request, Operation, System


# Modify to inject custom headers
def append_headers(headers):
    return headers


# Modify to change message to send
def process_event_message(event_message):
    return event_message
