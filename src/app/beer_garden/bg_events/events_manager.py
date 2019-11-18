from multiprocessing import Process, Queue

from beer_garden.bg_events.parent_listener import ParentListener
from brewtils.stoppable_thread import StoppableThread


class EventsManager(StoppableThread):

    def __init__(self):
        super().__init__(name="EventsManagerLogger")
        self.events_listeners = list()
        self.events_queue = Queue()

    def add_event(self, event_type, event):
        self.events_queue.put((event_type, event))

    def run(self):

        # While queue is not empty
        # Iterate over events and push them to their listeners

        self.logger.info("Event's Manager is running")

        while not self.wait(0.1):
            while not self.events_queue.empty():
                event_type, event = self.events_queue.get()

                event_processes = list()

                self.logger.info("Event's Manager is spawning processes")
                for event_listener in self.events_listeners:
                    process = Process(target=event_listener.receive_next_message, args=(event_type, event))
                    process.start()
                    event_processes.append(process)

                for process in event_processes:
                    process.join()

                self.logger.info("Event's Manager is closed processes")

    def register_listener(self, event_listener):
        self.events_listeners.append(event_listener)
        self.logger.info("Event's Manager is added listener")

    def build_listeners(self):
        self.register_listener(ParentListener())
