from brewtils.models import Event, Events, Operation
from requests import RequestException

import beer_garden.config as conf
from beer_garden.events.processors import QueueListener
from beer_garden.garden import local_garden, update_garden


class HttpParentUpdater(QueueListener):
    """Publish events using an EasyClient

    This will use the provided EasyClient to push events.

    In the event of a connection failure all events currently on the queue will be
    purged (!) and no new events will be accepted. Periodic attempts will be made to
    reestablish the connection, and normal behavior will resume if successful.

    """

    def __init__(self, easy_client=None, reconnect_action=None, **kwargs):
        self._ez_client = easy_client
        self._reconnect_action = reconnect_action
        self._connected = True

        super().__init__(
            logger_name=self.__module__ + "." + self.__class__.__name__, **kwargs
        )

    def put(self, event: Event) -> None:
        """Put a new item on the queue to be processed

        Will only add the item to the queue if currently connected to the parent.

        Args:
            event: The event to publish
        """
        if self._connected:
            self._queue.put(event)

    def process(self, event: Event):

        if event.error or (event.garden and event.garden != conf.get("garden.name")):
            return

        # TODO - This shouldn't be set here
        event.garden = conf.get("garden.name")
        if event.name in (
            Events.GARDEN_STARTED.name,
            Events.GARDEN_UPDATED.name,
            Events.GARDEN_STOPPED.name,
            Events.GARDEN_SYNC.name,
        ):
            if event.payload.parent is None and event.payload.name != event.garden:
                event.payload.parent = event.garden
                for connection in event.payload.publishing_connections:
                    connection.config = {}
                for connection in event.payload.receiving_connections:
                    connection.config = {}
                event.payload.has_parent = True

        try:
            operation = Operation(
                operation_type="PUBLISH_EVENT",
                model=event,
                model_type="Event",
                source_garden_name=conf.get("garden.name"),
            )
            self._ez_client.forward(operation)
        except RequestException as ex:
            self.logger.error(f"Error while publishing event to parent: {ex}")

            self._connected = False
            self._reconnect()

    def _update_garden_connection(self, status):
        garden = local_garden()

        for connection in garden.publishing_connections:
            if (
                connection.config["host"] == self._ez_client.client.bg_host
                and connection.config["port"] == self._ez_client.client.bg_port
                and connection.config["url_prefix"] == self._ez_client.client.bg_prefix
            ):
                connection.status = status

        update_garden(garden)

    def _reconnect(self):
        """Attempt to reestablish connection"""
        # Purge the current Queue
        while not self._queue.empty():
            self._queue.get()

        wait_time = 0.1
        while not self.stopped() and not self._connected:
            self.logger.warning("Attempting to reconnect to parent garden")

            try:
                if self._ez_client.can_connect():
                    self._connected = True

                    self.logger.warning("Successfully reconnected to parent garden")
                    self._update_garden_connection("PUBLISHING")

                    if self._reconnect_action:
                        self._reconnect_action()
            except RequestException:
                pass

            if not self._connected:
                self._update_garden_connection("UNREACHABLE")
                self.logger.debug("Waiting %.1f seconds before next attempt", wait_time)
                self.wait(wait_time)
                wait_time = min(wait_time * 2, 30)
