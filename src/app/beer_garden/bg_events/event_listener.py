

class EventListener:

    def receive_next_message(self, event_type, event):
        self.process_next_message(event_type, event)

    def process_next_message(self, event_type, event):
        pass

