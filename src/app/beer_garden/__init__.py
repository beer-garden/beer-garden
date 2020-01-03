# -*- coding: utf-8 -*-
import logging
import logging.config

from brewtils.models import RequestTemplate

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
]

# COMPONENTS #
application = None
logger = None

start_request = RequestTemplate(command="_start", command_type="EPHEMERAL")
stop_request = RequestTemplate(command="_stop", command_type="EPHEMERAL")


def signal_handler(signal_number, stack_frame):
    beer_garden.logger.info("Last call! Looks like we gotta close up.")
    beer_garden.application.stop()


def load_config(cli_args):
    global logger

    beer_garden.config.load(cli_args)
    beer_garden.log.load(beer_garden.config.get("log"))

    logger = logging.getLogger(__name__)
    logger.debug("Successfully loaded configuration")
