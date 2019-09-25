import wrapt

import beer_garden
from brewtils.models import Event, Events
from brewtils.schema_parser import SchemaParser


def publish_event(event_type):
    # TODO - This is kind of gross
    @wrapt.decorator(enabled=lambda: not getattr(beer_garden, "_running_tests", False))
    def wrapper(wrapped, _, args, kwargs):
        event = Event(name=event_type.name, payload="", error=False)

        try:
            result = wrapped(*args, **kwargs)
        except Exception as ex:
            event.error = True
            event.payload = str(ex)
            raise
        else:
            if event.name in (
                Events.INSTANCE_INITIALIZED.name,
                Events.INSTANCE_STARTED.name,
                Events.INSTANCE_STOPPED.name,
                Events.REQUEST_CREATED.name,
                Events.REQUEST_STARTED.name,
                Events.REQUEST_COMPLETED.name,
                Events.SYSTEM_CREATED.name,
                Events.SYSTEM_UPDATED.name,
            ):
                event.payload = SchemaParser.serialize(result, to_string=False)
            elif event.name in (Events.QUEUE_CLEARED.name, Events.SYSTEM_REMOVED.name):
                event.payload = {"id": args[0]}
        finally:
            beer_garden.application.event_publishers.publish_event(event)

        return result

    return wrapper
