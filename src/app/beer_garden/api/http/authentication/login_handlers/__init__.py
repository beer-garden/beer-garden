from typing import List, Type

from beer_garden import config

from .base import BaseLoginHandler
from .basic import BasicLoginHandler
from .trusted_header import TrustedHeaderLoginHandler

LOGIN_HANDLERS = [BasicLoginHandler, TrustedHeaderLoginHandler]


def enabled_login_handlers() -> List[Type[BaseLoginHandler]]:
    """Retrieve the list of login handlers that are currently enabled

    Returns:
        List[Type[BaseLoginHandler]]: List containing enabled login handler classes
    """
    config_root = "auth.authentication_handlers"
    handler_config_map = {
        "basic": BasicLoginHandler,
        "trusted_header": TrustedHeaderLoginHandler,
    }
    enabled_handlers = []

    for handler_config, handler_class in handler_config_map.items():
        config_path = f"{config_root}.{handler_config}.enabled"
        if config.get(config_path) is True:
            enabled_handlers.append(handler_class)

    return enabled_handlers
