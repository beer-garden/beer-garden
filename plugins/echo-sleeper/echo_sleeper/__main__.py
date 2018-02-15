from __future__ import absolute_import

from brewtils.plugin import PluginBase
from .client import EchoSleeperClient


if __name__ == '__main__':
    PluginBase(EchoSleeperClient()).run()
