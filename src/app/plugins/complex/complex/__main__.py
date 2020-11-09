from __future__ import absolute_import

import sys

from brewtils import get_argument_parser, get_connection_info, Plugin
from .client import ComplexClient

__version__ = "1.0.0.dev0"


def main():
    parser = get_argument_parser()
    parser.add_argument("instance_name")
    parser.add_argument("host")
    parser.add_argument("port")
    config = parser.parse_args(sys.argv[1:])

    Plugin(
        ComplexClient(config.host, config.port),
        name="complex",
        version=__version__,
        instance_name=config.instance_name,
        max_instances=2,
        **get_connection_info(cli_args=sys.argv[1:], argument_parser=parser)
    ).run()


if __name__ == "__main__":
    main()
