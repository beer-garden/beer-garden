from brewtils.stoppable_thread import StoppableThread
from multiprocessing import Queue


class EventListener(StoppableThread):

    def __init__(self):
        super().__init__()
        self.events_queue = Queue()

    def receive_next_message(self, event_type, event):
        self.events_queue.put((event_type, event))

    def process_next_message(self, event_type, event):
        pass

    def run(self):

        # While queue is not empty
        # Iterate over events and push them to their listeners

        while not self.wait(0.1):
            while not self.events_queue.empty():
                event_type, event = self.events_queue.get()
                self.process_next_message(event_type, event)
