import sys

from bg_utils.local_plugin import LocalPlugin
from sleeper.client import SleeperClient


def main():
    args = sys.argv
    if len(args) < 1:
        try:
            number_of_times_to_sleep = int(args[0])
        except (ValueError, TypeError):
            number_of_times_to_sleep = None
    else:
        number_of_times_to_sleep = None

    client = SleeperClient(number_of_times_to_sleep)
    plugin = LocalPlugin(client)
    plugin.run()


if __name__ == '__main__':
    main()
