from __future__ import absolute_import

import sys

from brewtils.plugin import PluginBase
from .client import ComplexClient
from .errors import StartupError


def main():
    if len(sys.argv) < 3:
        raise StartupError("2 arguments (host and port) are "
                           "required only %d was provided." % len(sys.argv))

    host = sys.argv[1]
    port = sys.argv[2]

    plugin = PluginBase(ComplexClient(host, port))
    plugin.run()


if __name__ == '__main__':
    main()
