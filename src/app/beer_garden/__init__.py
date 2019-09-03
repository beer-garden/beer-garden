import logging
import logging.config

import beer_garden.bg_utils
from beer_garden import config
from beer_garden import log
from beer_garden.__version__ import __version__
from beer_garden.app import BartenderApp
from beer_garden.errors import ConfigurationError
from brewtils.models import Request


# COMPONENTS #
application = None
logger = None

start_request = Request(command="_start", command_type="EPHEMERAL")
stop_request = Request(command="_stop", command_type="EPHEMERAL")


def setup_bartender(cli_args):
    global application, logger

    config.load(cli_args)
    log.setup_application_logging(config.get("log"))
    logger = logging.getLogger(__name__)

    application = BartenderApp()

    logger.debug("Successfully loaded the bartender application")


def progressive_backoff(func, stoppable_thread, failure_message):
    wait_time = 0.1
    while not stoppable_thread.stopped() and not func():
        logger.warning(failure_message)
        logger.warning("Waiting %.1f seconds before next attempt", wait_time)

        stoppable_thread.wait(wait_time)
        wait_time = min(wait_time * 2, 30)
