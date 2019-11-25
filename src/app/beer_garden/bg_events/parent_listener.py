from beer_garden.bg_events.event_listener import EventListener

import requests


class ParentListener(EventListener):
    """
    This is an example stubbed out for how parent listeners could publish events.
    """

    def __init__(self, config):
        """
        This API Endpoint has not been developed yet for V3.

        :param config:
        """
        super().__init__()
        self.endpoint = "{}://{}:{}{}api/v2/events".format(
            "https" if config.ssl.enabled else "http",
            config.public_fqdn,
            config.port,
            config.url_prefix,
        )

    def process_next_message(self, event):
        """
        Sends POST request to endpoint with the Event info.
        :param event: The Event to be processed
        :return:
        """
        r = requests.post(self.endpoint, json={"event": event})
