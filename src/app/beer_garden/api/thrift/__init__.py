import logging

import brewtils.thrift

from beer_garden.api.thrift.handler import BartenderHandler
from beer_garden.api.thrift.server import make_server

server = None


def run():
    global logger, server
    logger = logging.getLogger(__name__)

    # TODO: The thrift portion is currently hardcoded, because it should
    # no longer be in the config. Eventually the thrift thread will be removed.
    server = make_server(
        service=brewtils.thrift.bg_thrift.BartenderBackend,
        handler=BartenderHandler(),
        host="0.0.0.0",
        port=9090,
    )

    logger.info("Starting Thrift server")

    server.run()

    logger.info("Application is shut down. Goodbye!")


def stop():
    logger.info("Received a shutdown request.")
    server.stop()
