import requests

import beer_garden
from beer_garden.events.processors import QueueListener
from brewtils.models import Event


class HttpParentUpdater(QueueListener):
    """Publish events using an EasyClient"""

    def __init__(
        self, easy_client=None, black_list=None, reconnect_action=None, **kwargs
    ):
        super().__init__(**kwargs)

        self._ez_client = easy_client
        self._black_list = black_list or []
        self._reconnect_action = reconnect_action
        self._processing = True

    def put(self, item):
        """Put a new item on the queue to be processed

        Args:
            item: New item
        """
        if self._processing:
            self._queue.put(item)

    def process(self, event: Event):

        try:
            if event.name not in self._black_list:
                event.garden = beer_garden.config.get("garden.name")
                self._ez_client.publish_event(event)
        except requests.exceptions.ConnectionError:
            self.reconnect()

    def reconnect(self):

        self.logger.warning("Attempting to reconnect to Parent Garden")
        # Mark not processing and stop accepting events
        self._processing = False

        # Purge the current Queue
        while not self._queue.empty():
            self._queue.get()

        # Back-off connection from EZ Client
        wait_time = 0.1
        while not self.stopped() and not self._processing:
            if self._ez_client.can_connect():
                self._processing = True

                self.logger.warning("Successfully reconnected to Parent Garden")

                if self._reconnect_action:
                    self._reconnect_action()

            else:
                self.logger.debug("Waiting %.1f seconds before next attempt", wait_time)
                self.wait(wait_time)
                wait_time = min(wait_time * 2, 30)
