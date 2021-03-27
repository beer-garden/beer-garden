import datetime
import logging
import multiprocessing
from box import Box
from brewtils.models import Event, Events, Garden
from brewtils.stoppable_thread import StoppableThread
from typing import Iterable

import beer_garden.events
import beer_garden.router
from beer_garden.api.stomp.transport import Connection
from beer_garden.events import publish
from beer_garden.events.processors import QueueListener


class EventManager:
    """Will simply push events across the connection to the master process"""

    def __init__(self, conn):
        self._conn = conn

    def put(self, event):
        self._conn.send(event)


class StompManager(StoppableThread):
    """What is the purpose of this class??"""

    logger = logging.getLogger(__name__)

    @staticmethod
    def connect(stomp_config: Box, gardens: Iterable[Garden]) -> Connection:
        """Create and return a stomp connection

        Args:
            stomp_config:
            gardens:

        Returns:

        """
        conn = Connection(
            host_and_ports=[(stomp_config.get("host"), stomp_config.get("port"))],
            send_destination=stomp_config.get("send_destination"),
            subscribe_destination=stomp_config.get("subscribe_destination"),
            ssl=stomp_config.get("ssl"),
            username=stomp_config.get("username"),
            password=stomp_config.get("password"),
        )

        conn.connect(connected_message="connected", wait_time=0.1, gardens=gardens)

        return conn

    def __init__(self, ep_conn: multiprocessing.Pipe = None):
        """

        Args:
            ep_conn:
        """
        self.ep_conn = ep_conn
        self.conn_dict = {}

        self._setup_event_handling()
        self._setup_operation_forwarding()

        self.logger.debug("Starting forward processor")
        beer_garden.router.forward_processor.start()

        super().__init__(logger=self.logger, name="StompManager")

    def add_connection(self, stomp_config=None, name=None, is_main=False):
        host_and_ports = [(stomp_config.get("host"), stomp_config.get("port"))]
        subscribe_destination = stomp_config.get("subscribe_destination")
        ssl = stomp_config.get("ssl")

        use_ssl = ssl.get("use_ssl") or False
        conn_dict_key = f"{host_and_ports}{subscribe_destination}{use_ssl}"

        if conn_dict_key in self.conn_dict:
            if {"name": name, "main": is_main} not in self.conn_dict[conn_dict_key][
                "gardens"
            ]:
                self.conn_dict[conn_dict_key]["gardens"].append(
                    {"name": name, "main": is_main}
                )
        else:
            self.conn_dict[conn_dict_key] = {
                "conn": self.connect(stomp_config, [{"name": name, "main": is_main}]),
                "gardens": [{"name": name, "main": is_main}],
            }

        if "headers_list" not in self.conn_dict:
            self.conn_dict[conn_dict_key]["headers_list"] = []

        if stomp_config.get("headers") and is_main:
            headers = self.convert_header_to_dict(stomp_config.get("headers"))

            if headers not in self.conn_dict[conn_dict_key]["headers_list"]:
                self.conn_dict[conn_dict_key]["headers_list"].append(headers)

        return conn_dict_key

    def run(self):
        while not self.stopped():
            for value in self.conn_dict.values():
                conn = value["conn"]
                gardens = value["gardens"]

                if conn:
                    if not conn.is_connected() and conn.bg_active:
                        wait_time = value.get("wait_time") or 0.1
                        wait_date = value.get("wait_date")

                        if wait_date:
                            wait_check = datetime.datetime.utcnow() >= wait_date
                        else:
                            wait_check = True

                        if wait_check:
                            self.reconnect(
                                conn=conn, wait_time=wait_time, gardens=gardens
                            )
                            value["wait_time"] = min(wait_time * 2, 30)
                            seconds_added = datetime.timedelta(seconds=wait_time)
                            value["wait_date"] = (
                                datetime.datetime.utcnow() + seconds_added
                            )

                            if conn.is_connected():
                                value.pop("wait_time")
                                value.pop("wait_date")

            if self.ep_conn.poll():
                self.handle_event(self.ep_conn.recv())

        self.shutdown()

    def shutdown(self):
        self.logger.debug("Disconnecting connections")
        for value in self.conn_dict.values():
            value["conn"].disconnect()

        self.logger.debug("Stopping forward processing")
        beer_garden.router.forward_processor.stop()

        # This will almost definitely not be published because
        # it would need to make it up to the main process and
        # back down into this process. We just publish this
        # here in case the main process is looking for it.
        publish(
            Event(
                name=Events.ENTRY_STOPPED.name,
                metadata={"entry_point_type": "STOMP"},
            ),
        )

    def reconnect(self, conn=None, gardens=None, wait_time=None):
        if not conn.is_connected():
            self.logger.warning("Lost stomp connection")
            conn.connect(
                connected_message="reconnected", wait_time=wait_time, gardens=gardens
            )

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

            if event.payload.connection_type:
                if event.payload.connection_type.casefold() == "stomp":
                    stomp_config = self.format_connection_params(
                        "stomp_", event.payload.connection_params
                    )
                    stomp_config["send_destination"] = None
                    skip_key = self.add_connection(
                        stomp_config=stomp_config, name=event.payload.name
                    )

            self.remove_garden_from_list(
                garden_name=event.payload.name, skip_key=skip_key
            )

        for value in self.conn_dict.values():
            conn = value["conn"]
            if conn:
                if conn.is_connected() and conn.bg_active:
                    if value["headers_list"]:
                        for headers in value["headers_list"]:
                            conn.send(event, headers=headers)
                    else:
                        conn.send(event)

    @staticmethod
    def convert_header_to_dict(headers):
        tmp_headers = {}
        key_to_key = None
        key_to_value = None

        for header in headers:
            header = eval(header)

            for key in header.keys():
                if "key" in key:
                    key_to_key = key
                elif "value" in key:
                    key_to_value = key

            tmp_headers[header[key_to_key]] = header[key_to_value]

        return tmp_headers

    @staticmethod
    def format_connection_params(term, connection_params):
        """Strips leading term from connection parameters"""
        new_connection_params = {"ssl": {}}
        for key in connection_params:
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
