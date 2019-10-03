# -*- coding: utf-8 -*-
import logging
import signal

import brewtils.thrift

import beer_garden.config
from beer_garden.api.thrift.handler import BartenderHandler
from beer_garden.api.thrift.server import make_server

logger = None
the_server = None


def signal_handler(signal_number, stack_frame):
    stop()


def run(config, log_queue):
    global logger, the_server

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Absolute first thing to do is set the config
    beer_garden.config._CONFIG = config

    beer_garden.log.setup_entry_point_logging(log_queue)
    logger = logging.getLogger(__name__)

    # TODO: The thrift portion is currently hardcoded, because it should
    # no longer be in the config. Eventually the thrift thread will be removed.
    the_server = make_server(
        service=brewtils.thrift.bg_thrift.BartenderBackend,
        handler=BartenderHandler(),
        host="0.0.0.0",
        port=9090,
    )

    logger.info("Starting Thrift server")

    the_server.run()

    logger.info("Application is shut down. Goodbye!")


def stop():
    logger.info("Received a shutdown request.")
    the_server.stop()
