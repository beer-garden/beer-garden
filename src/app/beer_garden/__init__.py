# -*- coding: utf-8 -*-
import logging
import logging.config
from multiprocessing import Queue

from beer_garden.bg_events.events_manager import EventsManager
from beer_garden.bg_events.parent_http_processor import ParentHttpProcessor
from brewtils.models import Request

import beer_garden.bg_utils
import beer_garden.config
import beer_garden.log
from beer_garden.__version__ import __version__

__all__ = [
    "__version__",
    "application",
    "logger",
    "start_request",
    "stop_request",
    "load_config",
    #"events_manager",
    "events_queue"
]

# COMPONENTS #
application = None
logger = None
#events_manager = None
events_queue = None

start_request = Request(command="_start", command_type="EPHEMERAL")
stop_request = Request(command="_stop", command_type="EPHEMERAL")


def signal_handler(signal_number, stack_frame):
    beer_garden.logger.info("Last call! Looks like we gotta close up.")
    beer_garden.application.stop()

    if beer_garden.application.is_alive():
        beer_garden.application.join()

    beer_garden.logger.info("OK, we're all shut down. Have a good night!")


# def establish_events_manager():
#     global events_manager
#     events_manager = EventsManager()
#
#     global events_queue
#     events_queue = Queue()
#
#     events_manager.set_queue(events_queue)
#
#     event_config = beer_garden.config.get("event")
#     if event_config.parent.http.enable:
#         beer_garden.events_manager.register_listener(
#             ParentProcessor(event_config.parent.http)
#         )
#
#     beer_garden.events_manager.start()

def establish_events_queue(queue: Queue):
    global events_queue
    events_queue = queue


def load_config(cli_args):
    global logger

    beer_garden.config.load(cli_args)
    beer_garden.log.load(beer_garden.config.get("log"))

    logger = logging.getLogger(__name__)
    logger.debug("Successfully loaded configuration")
