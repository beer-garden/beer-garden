import logging
import logging.config

import bg_utils
import brewtils.rest
import bartender._version
from bartender.app import BartenderApp
from bartender.errors import ConfigurationError
from bartender.specification import get_default_logging_config
from brewtils.errors import ValidationError
from brewtils.rest.easy_client import EasyClient

__version__ = bartender._version.__version__

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

    application = BartenderApp()

    logger.debug("Successfully loaded the bartender application")


def progressive_backoff(func, stoppable_thread, failure_message):
    wait_time = 0.1
    while not stoppable_thread.stopped() and not func():
        logger.warning(failure_message)
        logger.warning("Waiting %.1f seconds before next attempt", wait_time)

        stoppable_thread.wait(wait_time)
        wait_time = min(wait_time * 2, 30)


def ensure_admin():
    # Either brew-view auth must be disabled (anonymous user will have bg-all)
    # or the user must have bg-all permissions
    try:
        bartender_user = bv_client.who_am_i()
    except ValidationError:
        raise ConfigurationError(
            "Unable to authenticate using provided username and password. "
            "This usually indicates an incorrect password - please check the "
            "web.username and web.password fields in the configuration."
        )

    if "bg-all" not in bartender_user.permissions:
        if config.web.username:
            raise ConfigurationError(
                'User "%s" does not have "bg-all" permission. Please check '
                "your configuration (specifically web.username and "
                "web.password fields)" % config.web.username
            )
        else:
            raise ConfigurationError(
                "It appears that Brew-view is operating with authentication "
                "enabled and no username / password was provided. Please check "
                "your configuration (specifically web.username and "
                "web.password fields)."
            )
