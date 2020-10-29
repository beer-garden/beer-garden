import logging
from brewtils.models import Event, Events
import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.processors import EventManager
from beer_garden.events import publish
from beer_garden.events.processors import QueueListener
from beer_garden.api.stomp.server import Connection
from brewtils.stoppable_thread import StoppableThread


class StompManager(StoppableThread):

    logger = logging.getLogger(__name__)

    def __init__(self, ep_conn, stomp_config):

        self.ep_conn = ep_conn
        host_and_ports = [(stomp_config.host, stomp_config.port)]
        self.conn = Connection(
            host_and_ports=host_and_ports,
            send_destination=stomp_config.get("send_destination"),
            subscribe_destination=stomp_config.get("subscribe_destination"),
            ssl=stomp_config.ssl,
            username=stomp_config.username,
            password=stomp_config.password,
        )
        self.conn.connect("connected")

        self._setup_event_handling()
        self._setup_operation_forwarding()
        self.logger.debug("Starting forward processor")
        beer_garden.router.forward_processor.start()
        super().__init__(logger=self.logger, name="StompManger")

    def run(self):
        while not self.stopped():
            self.reconnect()
            if self.ep_conn.poll():
                self.handle_event(self.ep_conn.recv())
        self.shutdown()

    def shutdown(self):
        self.conn.disconnect()
        self.logger.debug("Stopping forward processing")
        beer_garden.router.forward_processor.stop()
        # This will almost definitely not be published because
        # it would need to make it up to the main process and
        # back down into this process. We just publish this
        # here in case the main process is looking for it.
        publish(Event(name=Events.ENTRY_STOPPED.name))

    def reconnect(self):
        if not self.conn.is_connected():
            self.logger.warning("Lost stomp connection")
            self.conn.connect("reconnected")

    def handle_event(self, event):
        self.conn.send_event(event)

    @staticmethod
    def _setup_operation_forwarding():
        beer_garden.router.forward_processor = QueueListener(
            action=beer_garden.router.forward
        )

    def _setup_event_handling(self):
        # This will push all events generated in the entry point up to the master process
        beer_garden.events.manager = EventManager(self.ep_conn)
