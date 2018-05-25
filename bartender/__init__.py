import logging
import logging.config

import requests.exceptions

import bg_utils
import brewtils.rest
from bartender.app import BartenderApp
from bartender.specification import get_default_logging_config
from brewtils.rest.easy_client import EasyClient

# COMPONENTS #
application = None
config = None
logger = None
bv_client = None


def setup_bartender(spec, cli_args):
    global application, config, logger, bv_client

    config = bg_utils.load_application_config(spec, cli_args)
    config.web.url_prefix = brewtils.rest.normalize_url_prefix(config.web.url_prefix)

    log_default = get_default_logging_config(config.log.level, config.log.file)
    bg_utils.setup_application_logging(config, log_default)
    logger = logging.getLogger(__name__)

    bv_client = EasyClient(**config.web)

    application = BartenderApp(config)

    logger.debug("Successfully loaded the bartender application")


def connect_to_brew_view():
    try:
        logger.debug("Attempting to connect to Brew View")
        bv_client.find_systems()
        return True

    # This is a little annoying - we want to retry (return False) on a
    # ConnectionError but raise on subclasses (e.g. SSLError)
    except requests.exceptions.ConnectionError as ex:
        if type(ex) == requests.exceptions.ConnectionError:
            return False
        raise


def progressive_backoff(func, stoppable_thread, failure_message):
    wait_time = 0.1
    while not stoppable_thread.stopped() and not func():
        logger.warning(failure_message)
        logger.warning('Waiting %.1f seconds before next attempt', wait_time)

        stoppable_thread.wait(wait_time)
        wait_time = min(wait_time*2, 30)
