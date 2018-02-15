from __future__ import absolute_import

from brewtils.plugin import PluginBase
from .client import EchoClient


def main():
    plugin = PluginBase(EchoClient())
    plugin.run()


if __name__ == '__main__':
    main()
