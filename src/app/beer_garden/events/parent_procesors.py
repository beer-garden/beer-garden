import requests
import stomp
from brewtils.schema_parser import SchemaParser
import beer_garden.config as config
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


class StompParentUpdater(QueueListener):

    def __init__(
            self, black_list=None, reconnect_action=None, **kwargs
    ):
        super().__init__(**kwargs)
        stomp.logging.setLevel("WARN")
        stomp_config = config.get("parent.stomp")
        self.host_and_ports = [(stomp_config.host, stomp_config.port)]
        self.conn = None
        self.username = stomp_config.username
        self.password = stomp_config.password
        self.connect()
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
        if event.name not in self._black_list:
            event.garden = beer_garden.config.get("garden.name")
            if self.conn.is_connected():
                self.send(event)
            elif not self.conn.is_connected():
                self.reconnect()

    def send(self, event):
        stomp_config = config.get("parent.stomp")
        headers = {"model_class": event.__class__.__name__}
        message = SchemaParser.serialize(event, to_string=True,)
        self.conn.send(destination=stomp_config.event_destination, body=message, headers=headers)

    def connect(self):
        self.conn = stomp.Connection(host_and_ports=self.host_and_ports, heartbeats=(10000, 0))
        try:
            self.conn.connect(
                username=self.username,
                passcode=self.password,
                wait=True,
                headers={"client-id": self.username},
            )
        except Exception as e:
            self.logger.warning(str(e))

    def reconnect(self):

        self.logger.warning("Attempting to reconnect to Parent Garden")
        # Mark not processing and stop accepting events
        self._processing = False

        # Purge the current Queue
        while not self._queue.empty():
            self._queue.get()

        # Back-off connection from stomp
        wait_time = 0.1
        while not self.stopped() and not self._processing:
            self.connect()
            if self.conn.is_connected():
                self._processing = True
                self.logger.warning("Successfully reconnected to Parent Garden")
                if self._reconnect_action:
                    self._reconnect_action()
            if not self.conn.is_connected():
                self.logger.debug("Waiting %.1f seconds before next attempt", wait_time)
                self.wait(wait_time)
                wait_time = min(wait_time * 2, 30)
