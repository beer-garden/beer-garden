

import requests

from beer_garden.bg_events.events_manager import EventProcessor
from brewtils.schema_parser import SchemaParser


class ParentHttpProcessor(EventProcessor):
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
        requests.post(
            self.endpoint, json=SchemaParser.serialize(event, to_string=False)
        )
