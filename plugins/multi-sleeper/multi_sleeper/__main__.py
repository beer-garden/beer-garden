from __future__ import absolute_import

import sys

from brewtils.plugin import PluginBase
from .client import SleeperClient


def main():
    args = sys.argv
    if len(args) < 1:
        try:
            number_of_times_to_sleep = int(args[0])
        except (ValueError, TypeError):
            number_of_times_to_sleep = None
    else:
        number_of_times_to_sleep = None

    plugin = PluginBase(SleeperClient(number_of_times_to_sleep), max_concurrent=5)
    plugin.run()


if __name__ == '__main__':
    main()
