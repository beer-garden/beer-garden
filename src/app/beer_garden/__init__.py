# -*- coding: utf-8 -*-
import logging
import logging.config

from beer_garden.bg_events.events_manager import EventsManager
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
    "events_manager",
]

# COMPONENTS #
application = None
logger = None
events_manager = None

start_request = Request(command="_start", command_type="EPHEMERAL")
stop_request = Request(command="_stop", command_type="EPHEMERAL")


def signal_handler(signal_number, stack_frame):
    beer_garden.logger.info("Last call! Looks like we gotta close up.")
    beer_garden.application.stop()

    if beer_garden.application.is_alive():
        beer_garden.application.join()

    beer_garden.logger.info("OK, we're all shut down. Have a good night!")


def establish_events_manager():
    global events_manager
    events_manager = EventsManager()


def load_config(cli_args):
    global logger

    beer_garden.config.load(cli_args)
    beer_garden.log.load(beer_garden.config.get("log"))

    logger = logging.getLogger(__name__)
    logger.debug("Successfully loaded configuration")
