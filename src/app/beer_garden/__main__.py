#!/usr/bin/env python

import signal
import sys

import beer_garden
import beer_garden.api.http
import beer_garden.api.thrift
from beer_garden.app import Application
from beer_garden.config import generate_logging, generate, migrate


def generate_logging_config():
    generate_logging(sys.argv[1:])


def generate_config():
    generate(sys.argv[1:])


def migrate_config():
    migrate(sys.argv[1:])


def main():
    # Absolute first thing to do is load the config
    beer_garden.load_config(sys.argv[1:])

    # Need to create the application before registering the signal handlers
    beer_garden.application = Application()

    signal.signal(signal.SIGINT, beer_garden.signal_handler)
    signal.signal(signal.SIGTERM, beer_garden.signal_handler)

    beer_garden.logger.info("Hi! Please give me just a minute to get set up.")
    beer_garden.application.start()

    # Need to be careful here because a simple join() or wait() can cause the main
    # python thread to lock out our signal handler, which means we cannot shut down
    # gracefully in some circumstances. So instead we use pause() to wait on a
    # signal. If you choose to change this please test thoroughly when deployed via
    # system packages (apt/yum) as well as python packages and docker.
    # Thanks! :)
    signal.pause()

    beer_garden.logger.info("Don't forget to drive safe!")


if __name__ == "__main__":
    main()
