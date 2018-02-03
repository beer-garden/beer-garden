import json
import logging
import logging.config
import time
from io import open

from requests.exceptions import RequestException

import bg_utils
import brewtils.rest
from bartender.app import BartenderApp
from bartender.specification import get_default_logging_config
from brewtils.rest.easy_client import EasyClient

# DEFAULTS #
config = None

# COMPONENTS #
application = None
logger = None
bv_client = None


def setup_bartender(spec, cli_args):
    global application, config, logger, bv_client

    # We load the config once just to see if there is a config file we should load from.
    temp_config = spec.load_app_config(cli_args, 'ENVIRONMENT')

    # If they specified a config file, we should load it up
    if temp_config.config:
        with open(temp_config.config) as config_file:
            config_from_file = json.load(config_file)
    else:
        config_from_file = {}

    config = spec.load_app_config(cli_args, config_from_file, 'ENVIRONMENT')

    prefix = brewtils.rest.normalize_url_prefix(config.url_prefix)
    config['url_prefix'] = prefix
    config.url_prefix = prefix

    bg_utils.setup_application_logging(config, get_default_logging_config(config.log_level, config.log_file))
    logger = logging.getLogger(__name__)

    bg_utils.setup_database(config)

    bv_client = EasyClient(config.web_host, config.web_port, ssl_enabled=config.ssl_enabled,
                           ca_cert=config.ca_cert, url_prefix=config.url_prefix, ca_verify=config.ca_verify)

    application = BartenderApp(config)

    # Ensure we have a message queue connection
    _progressive_backoff(application.clients['pyrabbit'].is_alive, 'message queue')

    # Ensure we have a brew-view connection
    _progressive_backoff(_connect_to_brew_view, 'Brew-View')

    logger.debug("Successfully loaded the bartender application")


def _connect_to_brew_view():
    try:
        logger.debug("Attempting to connect to Brew View")
        bv_client.find_systems()
        return True
    except RequestException:
        return False


def _progressive_backoff(func, name):
    wait_time = 0.1
    while not func():
        logger.warning('Could not connect to %s, waiting %f seconds before next attempt', name, wait_time)
        time.sleep(wait_time)
        wait_time = min(wait_time*2, 30)
