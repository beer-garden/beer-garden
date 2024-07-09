# -*- coding: utf-8 -*-
import asyncio
import logging
from datetime import datetime, timezone
from functools import partial

import wrapt
from brewtils.models import Event, Events

from beer_garden import config as config

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
    try:
        # Do some formatting / tweaking
        if not event.garden:
            event.garden = config.get("garden.name")
        if not event.timestamp:
            event.timestamp = datetime.now(timezone.utc)

        return manager.put(event)
    except Exception as ex:
        logger.exception(f"Error publishing event: {ex}")


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
        # Allows for conditionally disabling publishing
        _publish_success = kwargs.pop("_publish_success", True)
        _publish_error = kwargs.pop("_publish_error", True)

        event = Event(name=event_type.name)

        try:
            result = wrapped(*args, **kwargs)

            event.payload_type = result.__class__.__name__
            event.payload = result

            return result
        except Exception as ex:
            event.error = True
            event.error_message = str(ex)

            raise
        finally:
            if (not event.error and _publish_success) or (
                event.error and _publish_error
            ):
                publish(event)

    return wrapper


def publish_event_async(event_type: Events):
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
        task = asyncio.ensure_future(wrapped(*args, **kwargs))
        task.add_done_callback(partial(_async_callback, event_type=event_type))

        return task

    return wrapper


def _async_callback(task, event_type=None):
    event = Event(name=event_type.name)

    try:
        result = task.result()

        event.payload_type = result.__class__.__name__
        event.payload = result
    except Exception as ex:
        event.error = True
        event.error_message = str(ex)
    finally:
        try:
            publish(event)
        except Exception as ex:
            logger.exception(f"Error publishing event: {ex}")
