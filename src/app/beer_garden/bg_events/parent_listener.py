from beer_garden.bg_events.event_listener import EventListener

import requests


class ParentListener(EventListener):

    def __init__(self):
        self.parent_uri = 'http://localhost:8002/api/v2/events'
        pass

    def process_next_message(self, event_type, event):

        r = requests.post(self.parent_uri, json={'event_type': event_type,
                                                 'event': event})

