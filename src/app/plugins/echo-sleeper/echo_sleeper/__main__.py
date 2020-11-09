from __future__ import absolute_import

import sys

from brewtils import get_connection_info, Plugin
from .client import EchoSleeperClient

__version__ = "1.0.0.dev0"


def main():
    connection_params = get_connection_info(sys.argv[1:])

    Plugin(
        EchoSleeperClient(connection_params),
        name="echo-sleeper",
        version=__version__,
        **connection_params
    ).run()


if __name__ == "__main__":
    main()
