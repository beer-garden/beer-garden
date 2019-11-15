# -*- coding: utf-8 -*-
import logging
import os
import types

import thriftpy2

from beer_garden.api.thrift.handler import BartenderHandler
from beer_garden.api.thrift.server import make_server

logger = None
the_server = None

bg_thrift = thriftpy2.load(
    os.path.join(os.path.dirname(__file__), "beergarden.thrift"),
    module_name="bg_thrift",
)


def run():
    global logger, the_server
    logger = logging.getLogger(__name__)

    # TODO: The thrift portion is currently hardcoded, because it should
    # no longer be in the config. Eventually the thrift thread will be removed.
    the_server = make_server(
        service=bg_thrift.BartenderBackend,
        handler=BartenderHandler(),
        host="0.0.0.0",
        port=9090,
    )

    logger.info("Starting Thrift server")

    the_server.run()

    logger.info("Thrift server is shut down. Goodbye!")


def signal_handler(_: int, __: types.FrameType):
    the_server.stop()
