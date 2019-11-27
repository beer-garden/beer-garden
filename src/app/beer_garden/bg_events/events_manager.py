from multiprocessing import Queue

from brewtils.stoppable_thread import StoppableThread
from brewtils.models import Event

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

    def __init__(self, events_queue):
        super().__init__(name="EventsManagerLogger")
        self.events_listeners = list()
        self.events_queue = events_queue

    def add_event(self, event: Event):
        """Add event to the management queue

        :param event: The Event to be published
        """
        self.events_queue.put(event)

    def set_queue(self, events_queue: Queue):
        self.events_queue = events_queue

    def run(self):
        """
        Processes events while Manager is active
        """
        while not self.wait(0.1):
            while not self.events_queue.empty():
                event = self.events_queue.get()
                for event_listener in self.events_listeners:
                    event_listener.receive_next_message(event)

        for event_listener in self.events_listeners:
            event_listener.stop()

    def register_listener(self, event_listener: EventProcessor):
        """Register and start an EventsListener

        :param event_listener: Register an EventsListener
        """
        event_listener.start()
        self.events_listeners.append(event_listener)
