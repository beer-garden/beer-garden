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

    @staticmethod
    def connect(stomp_config):
        conn = Connection(
            host_and_ports=[(stomp_config.get("host"), stomp_config.get("port"))],
            send_destination=stomp_config.get("send_destination"),
            subscribe_destination=stomp_config.get("subscribe_destination"),
            ssl=stomp_config.get("ssl"),
            username=stomp_config.get("username"),
            password=stomp_config.get("password"),
        )
        conn.connect("connected")
        return conn

    def __init__(self, ep_conn=None, stomp_config=None, name=None, is_main=True):
        self.conn_dict = {}
        self.ep_conn = ep_conn
        if stomp_config:
            host_and_ports = [(stomp_config.get("host"), stomp_config.get("port"))]
            subscribe_destination = stomp_config.get("subscribe_destination")
            ssl = stomp_config.get("ssl")
            self.conn_dict[f"{host_and_ports}{subscribe_destination}{ssl.get('use_ssl')}"] = {
                "conn": self.connect(stomp_config),
                "gardens": [{"name": name, "main": is_main}]
            }

        self._setup_event_handling()
        self._setup_operation_forwarding()
        self.logger.debug("Starting forward processor")
        beer_garden.router.forward_processor.start()
        super().__init__(logger=self.logger, name="StompManager")

    def run(self):
        while not self.stopped():
            if self.ep_conn.poll():
                self.handle_event(self.ep_conn.recv())
        self.shutdown()

    def shutdown(self):
        for value in self.conn_dict.values():
            conn = value["conn"]
            conn.disconnect()
        self.logger.debug("Stopping forward processing")
        beer_garden.router.forward_processor.stop()
        # This will almost definitely not be published because
        # it would need to make it up to the main process and
        # back down into this process. We just publish this
        # here in case the main process is looking for it.
        publish(Event(name=Events.ENTRY_STOPPED.name))

    def reconnect(self, conn):
        if not conn.is_connected():
            self.logger.warning("Lost stomp connection")
            conn.connect("reconnected")

    def remove_garden_from_list(self, garden_name=None, skip_key=None):
        """removes garden name from dict list of gardens for stomp subscriptions"""
        for key in list(self.conn_dict):
            if not key == skip_key:
                gardens = self.conn_dict[key]["gardens"]
                for garden in gardens:
                    if garden_name == garden["name"] and not garden["main"]:
                        gardens.remove(garden)
                if not gardens:
                    self.conn_dict[key]["conn"].disconnect()
                    self.conn_dict.pop(key)

    def handle_event(self, event):
        if event.name == Events.GARDEN_REMOVED.name:
            self.remove_garden_from_list(garden_name=event.payload.name)

        elif event.name == Events.GARDEN_UPDATED.name:
            skip_key = None
            if event.payload.connection_type.casefold() == "stomp":
                stomp_config = self.format_connection_params("stomp_", event.payload.connection_params)
                stomp_config["send_destination"] = None
                skip_key = self.add_connection(stomp_config=stomp_config, name=event.payload.name)
            self.remove_garden_from_list(garden_name=event.payload.name, skip_key=skip_key)
        for value in self.conn_dict.values():
            conn = value["conn"]
            if conn:
                self.reconnect(conn)
                conn.send_event(event)

    def add_connection(self, stomp_config=None, name=None, is_main=False):
        host_and_ports = [(stomp_config.get("host"), stomp_config.get("port"))]
        subscribe_destination = stomp_config.get("subscribe_destination")
        ssl = stomp_config.get("ssl")
        use_ssl = ssl.get('use_ssl') or False
        conn_dict_key = f"{host_and_ports}{subscribe_destination}{use_ssl}"
        if conn_dict_key in self.conn_dict:
            if ({"name": name, "main": is_main} not in
                    self.conn_dict[conn_dict_key]["gardens"]):
                self.conn_dict[conn_dict_key]["gardens"].append(
                    {"name": name, "main": is_main}
                )
        else:
            self.conn_dict[conn_dict_key] = {
                "conn": self.connect(stomp_config),
                "gardens": [{"name": name, "main": is_main}]
            }
        return conn_dict_key

    @staticmethod
    def format_connection_params(term, connection_params):
        """Strips leading term from connection parameters and formats dictionary
        to match corresponding entry point config for connection type"""
        new_connection_params = {"ssl": {}}
        for key in connection_params:
            if "ssl" in key:
                new_connection_params["ssl"][
                    key.replace(term + "ssl_", "")
                ] = connection_params[key]
            else:
                new_connection_params[key.replace(term, "")] = connection_params[key]
        return new_connection_params

    @staticmethod
    def _setup_operation_forwarding():
        beer_garden.router.forward_processor = QueueListener(
            action=beer_garden.router.forward
        )

    def _setup_event_handling(self):
        # This will push all events generated in the entry point up to the master process
        beer_garden.events.manager = EventManager(self.ep_conn)
