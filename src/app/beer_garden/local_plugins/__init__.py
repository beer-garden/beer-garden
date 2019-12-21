# -*- coding: utf-8 -*-
from enum import Enum

CONFIG_NAME = "beer.conf"


class ConfigKeys(Enum):
    PLUGIN_ENTRY = 1
    INSTANCES = 2
    PLUGIN_ARGS = 3
    ENVIRONMENT = 4
    LOG_LEVEL = 5

    NAME = 6
    VERSION = 7
    DESCRIPTION = 8
    MAX_INSTANCES = 9
    ICON_NAME = 10
    DISPLAY_NAME = 11
    METADATA = 12
