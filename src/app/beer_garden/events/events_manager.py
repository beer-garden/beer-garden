# -*- coding: utf-8 -*-
import logging

import wrapt
from brewtils.models import Event, Events

# In this master process this should be an instance of EventManager, and in entry points
# it should be an instance of EntryPointManager
manager = None

logger = logging.getLogger(__name__)


def publish(event: Event) -> None:
    """Convenience method for publishing events

    All this does is place the event on the queue for the process-wide manager to pick
    up and process.

    Args:
        event: The event to publish

    Returns:
        None
    """
    return manager.put(event)


def publish_event(event_type: Events):
    """Decorator that will result in an event being published

    This will attempt to publish an event regardless of whether the underlying function
    raised or completed normally.

    If the wrapped function raises the exception will be re-raised.

    The event publishing *itself* will not raise anything. Any exceptions generated
    during publishing will be logged as such, but WILL NOT BE RAISED.

    Args:
        event_type: The Event type

    Raises:
        Any: If the underlying function raised an exception it will be re-raised

    Returns:
        Any: The wrapped function result
    """

    @wrapt.decorator
    def wrapper(wrapped, _, args, kwargs):
        result = None
        error = False

        try:
            # Make sure to save result here so it can be used in the finally block
            result = wrapped(*args, **kwargs)

            return result
        except Exception as ex:
            result = ex
            error = True
            raise
        finally:
            try:
                publish(
                    _create_event(
                        event_type=event_type,
                        payload=result,
                        error=error,
                        args=args,
                        kwargs=kwargs,
                    )
                )
            except Exception as ex:
                logger.exception(f"Error publishing event: {ex}")

    return wrapper


def _create_event(
    event_type: Events, payload, error: bool, args=None, kwargs=None
) -> Event:
    """Internal helper function for publishing an event from a function invocation

    Args:
        event_type: The event type
        payload: Payload
        error: Event error flag
        args: The positional arguments for the wrapped function
        kwargs: The keyword arguments for the wrapped function

    Returns:
        None
    """
    # TODO - We really need to standardize what an event looks like

    event = Event(name=event_type.name, payload=payload, error=error)

    # The payload is an exception, so just stringify it
    if error:
        event.payload = str(payload)

    else:
        if event.name in (Events.REQUEST_UPDATED.name, Events.SYSTEM_UPDATED.name):
            event.metadata = args[1]
        elif event.name in (Events.QUEUE_CLEARED.name, Events.SYSTEM_REMOVED.name):
            event.payload = {"id": args[0]}
        elif event.name in (Events.DB_DELETE.name,):
            event.payload = args[0]

    return event
