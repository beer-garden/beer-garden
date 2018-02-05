import sys

from bg_utils.local_plugin import LocalPlugin
from complex.client import ComplexClient
from complex.errors import StartupError


def main():
    if len(sys.argv) < 3:
        raise StartupError("2 arguments (host and port) are required only %d was provided." % len(sys.argv))

    host = sys.argv[1]
    port = sys.argv[2]

    plugin = LocalPlugin(ComplexClient(host, port))
    plugin.run()

if __name__ == '__main__':
    main()
