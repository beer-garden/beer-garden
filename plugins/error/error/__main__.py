from __future__ import absolute_import

from brewtils.plugin import PluginBase
from .client import ErrorClient


def main():
    plugin = PluginBase(ErrorClient())
    plugin.run()


if __name__ == '__main__':
    main()
