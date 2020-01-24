# -*- coding: utf-8 -*-
import wrapt
from brewtils.models import Event, Events

# In this master process this should be an instance of EventManager, and in entry points
# it should be an instance of EntryPointManager
manager = None


class EventManagerBase:
    """Base event manager"""

    def do_publish(self, event):
        pass

    def create_event(self, name, payload, error, args=None, kwargs=None):
        event = Event(name=name, payload=payload, error=error)

        if error:
            # here the payload is an exception, so just stringify it
            event.payload = str(payload)

        else:
            if event.name in (
                Events.INSTANCE_UPDATED.name,
                Events.REQUEST_UPDATED.name,
                Events.SYSTEM_UPDATED.name,
            ):
                event.metadata = args[1]
            elif event.name in (Events.QUEUE_CLEARED.name, Events.SYSTEM_REMOVED.name):
                event.payload = {"id": args[0]}
            elif event.name in (Events.DB_DELETE.name,):
                event.payload = args[0]

        self.do_publish(event)


class MainEventManager(EventManagerBase):
    """Will be used to appropriately route events.

    This will be the main process's manager.
    """

    def do_publish(self, event):
        pass


class EntryPointManager(EventManagerBase):
    """Will be used to manage events from an entry point perspective

    This basically ships event up to the main process.
    """

    def __init__(self, conn):
        self.conn = conn

    def do_publish(self, event):
        self.conn.send(event)


def publish_event(event_type):
    @wrapt.decorator
    def wrapper(wrapped, _, args, kwargs):
        try:
            result = wrapped(*args, **kwargs)

            manager.create_event(event_type.name, result, False, args, kwargs)

            return result
        except Exception as ex:
            manager.create_event(event_type.name, ex, True, args, kwargs)
            raise

    return wrapper
