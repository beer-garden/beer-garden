# -*- coding: utf-8 -*-
from multiprocessing import Queue

import wrapt
from brewtils.models import Event, Events
from brewtils.schema_parser import SchemaParser
from brewtils.stoppable_thread import StoppableThread

import beer_garden

# In entry point processes this will be used to ship events back to the master process
upstream_queue = None


def set_upstream(queue: Queue) -> None:
    global upstream_queue
    upstream_queue = queue


class EventProcessor(StoppableThread):
    """
    Base class for Event Listeners
    """

    def __init__(self):
        super().__init__()
        self.events_queue = Queue()

    def receive_next_message(self, event):
        """
        Accepts new messages for the Events Listener to process in the order that are received

        :param event: The Event to be published
        """

        self.events_queue.put(event)

    def process_next_message(self, event):
        """
        Stubbed out for classes to overwrite with their logic.

        :param event: The Event to be published
        :return:
        """
        pass

    def clear_queue(self):
        # Stop accepting events so Beergarden can stop

        # Purge local queue to prevent future processes
        while not self.events_queue.empty():
            self.events_queue.get()

    def run(self):
        """
        Processes events while Listener is active
        """

        while not self.wait(0.1):
            while not self.events_queue.empty():
                event = self.events_queue.get()
                self.process_next_message(event)


class EventsManager(StoppableThread):
    """
    Class to accept multiple events and forward to Event Listeners running is separate threads
    """

    events_queue = None

    def __init__(self, queue):
        super().__init__(name="EventsManagerLogger")
        self.event_processors = list()
        self.events_queue = queue

    def add_event(self, event: Event):
        """Add event to the management queue

        :param event: The Event to be published
        """
        self.events_queue.put(event)

    def run(self):
        """
        Processes events while Manager is active
        """
        while not self.wait(0.1):
            while not self.events_queue.empty():
                event = self.events_queue.get()
                for event_processor in self.event_processors:
                    event_processor.receive_next_message(event)

        for event_processor in self.event_processors:
            event_processor.stop()

    def register_processor(self, event_processor: EventProcessor):
        """Register and start an EventProcessor

        :param event_processor: Register an EventProcessor
        """
        event_processor.start()
        self.event_processors.append(event_processor)


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
            ):
                event.payload = result
            elif event.name in (
                Events.INSTANCE_UPDATED.name,
                Events.REQUEST_UPDATED.name,
                Events.SYSTEM_UPDATED.name,
            ):
                event.payload = result
                event.metadata = args[1]
            elif event.name in (Events.QUEUE_CLEARED.name, Events.SYSTEM_REMOVED.name):
                event.payload = {"id": args[0]}
            elif event.name in (Events.DB_CREATE.name, Events.DB_UPDATE.name):
                event.payload = result
            elif event.name in (Events.DB_DELETE.name,):
                event.payload = args[0]
        finally:
            upstream_queue.put(event)

        return result

    return wrapper
