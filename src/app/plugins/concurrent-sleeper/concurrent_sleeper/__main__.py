import sys
import time

from brewtils import get_connection_info, parameter, system, Plugin

__version__ = "1.0.0.dev0"


@system
class SleeperClient:
    @parameter(
        key="amount", type="Float", description="Amount of time to sleep (in seconds)"
    )
    def sleep(self, amount):
        print("About to sleep for %d" % amount)
        time.sleep(amount)
        print("I'm Awake!")


def main():
    Plugin(
        SleeperClient(),
        name="concurrent-sleeper",
        version=__version__,
        max_concurrent=5,
        **get_connection_info(sys.argv[1:])
    ).run()


if __name__ == "__main__":
    main()
