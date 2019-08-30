#!/usr/bin/env python

import signal
import sys
from argparse import ArgumentParser

from yapconf import YapconfSpec

import bg_utils
import brew_view
from brew_view.specification import SPECIFICATION, get_default_logging_config


def signal_handler(signal_number, stack_frame):
    brew_view.logger.info("Received a shutdown request.")
    brew_view.io_loop.add_callback_from_signal(brew_view.shutdown)


def generate_logging_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.generate_logging_config_file(
        spec, get_default_logging_config, sys.argv[1:]
    )


def generate_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.generate_config_file(spec, sys.argv[1:])


def migrate_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.update_config_file(spec, sys.argv[1:])


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    parser = ArgumentParser()
    spec.add_arguments(parser)
    args = parser.parse_args(sys.argv[1:])

    # Logging isn't set up until after this...
    brew_view.setup(spec, vars(args))

    # Schedule things to happen after the ioloop comes up
    brew_view.io_loop.add_callback(brew_view.startup)

    brew_view.logger.info("Starting IO loop")
    brew_view.io_loop.start()

    brew_view.logger.info("Application is shut down. Goodbye!")


if __name__ == "__main__":
    main()
