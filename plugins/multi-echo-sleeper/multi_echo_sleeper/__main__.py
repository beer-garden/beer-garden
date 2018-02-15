from __future__ import absolute_import

import os

from brewtils import get_bg_connection_parameters
from brewtils.plugin import PluginBase
from brewtils.rest.system_client import SystemClient
from .client import EchoSleeperClient


def main():
    params = get_bg_connection_parameters()

    plugin = PluginBase(
        EchoSleeperClient(SystemClient(system_name='echo', **params),
                          SystemClient(system_name='sleeper', **params)),
        max_concurrent=5)
    plugin.run()


if __name__ == '__main__':
    main()
