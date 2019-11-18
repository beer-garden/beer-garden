from beer_garden.bg_events.event_listener import EventListener

import requests


# from requests import Session

class ParentListener(EventListener):

    def __init__(self, config):
        self.endpoint = '{}://{}:{}{}api/v2/events'.format('https' if config.ssl.enabled else 'http', config.public_fqdn,
                                                           config.port, config.url_prefix)

    def process_next_message(self, event_type, event):
        r = requests.post(self.endpoint, json={'event_type': event_type,
                                               'event': event})
