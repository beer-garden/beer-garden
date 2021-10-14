#!/usr/bin/env python

import argparse
import logging
import signal
import sys
from pathlib import Path

import beer_garden
import beer_garden.config
import beer_garden.log
from beer_garden.app import Application


def generate_config():
    beer_garden.config.generate(sys.argv[1:])


def migrate_config():
    beer_garden.config.migrate(sys.argv[1:])


def generate_app_logging_config():
    beer_garden.config.generate_app_logging(sys.argv[1:])


def generate_plugin_logging_config():
    beer_garden.config.generate_plugin_logging(sys.argv[1:])


def deprecate_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", dest="file")
    parsed = vars(parser.parse_known_args()[0])

    existing_path = Path(parsed["file"]).resolve()
    if existing_path.exists():
        new_path = Path(parsed["file"] + ".old").resolve()
        existing_path.rename(new_path)


def noop():
    pass


def main():
    # Absolute first thing to do is load the config
    beer_garden.config.load(sys.argv[1:])

    # Then configure logging
    beer_garden.log.load(beer_garden.config.get("log"))
    logger = logging.getLogger(__name__)

    # Need to create the application before registering the signal handlers
    beer_garden.application = Application()

    signal.signal(signal.SIGINT, beer_garden.signal_handler)
    signal.signal(signal.SIGTERM, beer_garden.signal_handler)

    logger.info("Hi! Please give me just a minute to get set up.")
    beer_garden.application.start()

    # Need to be careful here because a simple join() or wait() can cause the main
    # python thread to lock out our signal handler, which means we cannot shut down
    # gracefully in some circumstances. So instead we use pause() to wait on a
    # signal. If you choose to change this please test thoroughly when deployed via
    # system packages (apt/yum) as well as python packages and docker.
    # Thanks! :)
    signal.pause()

    if beer_garden.application.is_alive():
        beer_garden.application.join()

    logger.info("OK, we're all shut down. Have a good night!\n")


if __name__ == "__main__":
    main()
