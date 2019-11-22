from brewtils.stoppable_thread import StoppableThread
from multiprocessing import Queue


class EventListener(StoppableThread):
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
                event_type, event = self.events_queue.get()
                self.process_next_message(event_type, event)
