#!/usr/bin/env python

"""Runnable entrypoint for **only** the HTTP package.

WARNING: THIS IS PURELY FOR DEBUGGING PURPOSES. NORMALLY THIS WILL NOT BE RUN!!

Like the warning says - normally the main application should run this module as an
EntryPoint. However, there was a time when it was necessary to see if the EntryPoint
structure itself was causing issues. This was created to allow the HTTP package to be
run in a completely standalone mode.

"""

import logging
import signal

import sys

import beer_garden
import beer_garden.config
import beer_garden.db.api as db
import beer_garden.log
import beer_garden.queue.api as queue
import beer_garden.router as router
from beer_garden.api.http import run, signal_handler


def generate_config():
    beer_garden.config.generate(sys.argv[1:])


def migrate_config():
    beer_garden.config.migrate(sys.argv[1:])


def generate_app_logging_config():
    beer_garden.config.generate_app_logging(sys.argv[1:])


def generate_plugin_logging_config():
    beer_garden.config.generate_plugin_logging(sys.argv[1:])


def main():
    # Absolute first thing to do is load the config
    beer_garden.config.load(sys.argv[1:])

    # Then configure logging
    beer_garden.log.load(beer_garden.config.get("log"))
    logger = logging.getLogger(__name__)

    # Set up plugin logging
    beer_garden.log.load_plugin_log_config()

    # Set up a database connection
    db.create_connection(use_motor=True, db_config=beer_garden.config.get("db"))

    # Set up message queue connections
    queue.create_clients(beer_garden.config.get("mq"))

    # Load known gardens for routing
    router.setup_routing()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Hi! Please give me just a minute to get set up.")

    run()

    logger.info("OK, we're all shut down. Have a good night!")


if __name__ == "__main__":
    main()
