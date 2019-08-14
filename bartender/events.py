import wrapt

import bartender
from brewtils.models import Event, Events


def publish_event(event_type):
    @wrapt.decorator
    def wrapper(wrapped, _, args, kwargs):
        event = Event(name=event_type.name)

        result = None
        payload = None
        error = False

        try:
            result = wrapped(*args, **kwargs)
        except Exception:
            event.error = True
            raise
        finally:
            if event.name.startswith("REQUEST"):
                event.payload = {
                    k: str(getattr(result, k))
                    for k in [
                        "id",
                        "command",
                        "system",
                        "system_version",
                        "instance_name",
                    ]
                }
            elif event.name == Events.SYSTEM_CREATED.name:
                event.payload = {"id": str(result.id)}

            elif event.name.startswith("SYSTEM"):
                event.payload = {"id": args[0]}

            elif event.name.startswith("INSTANCE"):
                event.payload = {"id": args[0]}

            elif event.name == Events.QUEUE_CLEARED.name:
                event.payload = {"queue_name": args[0]}

            bartender.application.event_publishers.publish_event(event)

        return result

    return wrapper
