import logging
import types

import beer_garden.config as config
from brewtils.models import Event, Events
import beer_garden.events
import beer_garden.router
import threading
from beer_garden.api.stomp.processors import EventManager
from beer_garden.events import publish
from beer_garden.events.processors import QueueListener
from beer_garden.api.stomp.server import Connection

logger = logging.getLogger(__name__)
stop_thread = False


def shutdown():
    global stop_thread
    stop_thread = True


class StompManager:
    def __init__(self, ep_conn, stomp_config):
        self.ep_conn = ep_conn
        host_and_ports = [(stomp_config.host, stomp_config.port)]
        self.conn = Connection(
            host_and_ports=host_and_ports,
            send_destination=stomp_config.get("event_destination"),
            subscribe_destination=stomp_config.get("operation_destination"),
            ssl=stomp_config.ssl,
            username=stomp_config.username,
            password=stomp_config.password,
        )
        self.conn.connect("connected")

        self._setup_event_handling()
        self._setup_operation_forwarding()
        logger.debug("Starting forward processor")
        beer_garden.router.forward_processor.start()
        self.stomp_thread = threading.Thread(self._event_thread())

    def start_thread(self):
        self.stomp_thread.start()

    def _event_thread(self):
        while True:
            self.reconnect()
            if self.ep_conn.poll():
                self.handle_event(self.ep_conn.recv())
            if stop_thread:
                self.conn.disconnect()
                logger.debug("Stopping forward processing")
                beer_garden.router.forward_processor.stop()
                # This will almost definitely not be published because it would need to make it up
                # to the main process and back down into this process. We just publish this here in
                # case the main process is looking for it.
                publish(Event(name=Events.ENTRY_STOPPED.name))
                break

    def reconnect(self):
        if not self.conn.is_connected():
            logger.warning("Lost stomp connection")
            self.conn.connect("reconnected")

    def handle_event(self, event):
        self.conn.send_event(event)

    def _setup_operation_forwarding(self):
        beer_garden.router.forward_processor = QueueListener(
            action=beer_garden.router.forward
        )

    def _setup_event_handling(self):
         # This will push all events generated in the entry point up to the master process
        beer_garden.events.manager = EventManager(self.ep_conn)
