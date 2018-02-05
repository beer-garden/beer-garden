#!/usr/bin/env python

import signal
import bg_utils
import sys
from argparse import ArgumentParser
from app_config import ConfigSpec

import bartender
from bartender.specification import SPECIFICATION, get_default_logging_config


def signal_handler(signal_number, stack_frame):
    bartender.logger.info("Last call! Looks like we gotta shut down.")
    bartender.application.stop()

    bartender.logger.info("Closing time! You don't have to go home, but you can't stay here.")
    bartender.application.join()

    bartender.logger.info("Looks like the Application is shut down. Have a good night!")


def generate_logging_config():
    spec = ConfigSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.generate_logging_config(spec, get_default_logging_config, sys.argv[1:])


def generate_config():
    spec = ConfigSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.generate_config(spec, sys.argv[1:])


def migrate_config():
    spec = ConfigSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.migrate_config(spec, sys.argv[1:])


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    spec = ConfigSpec(SPECIFICATION, env_prefix="BG_")
    parser = ArgumentParser()
    spec.add_arguments_to_parser(parser)
    args = parser.parse_args(sys.argv[1:])

    bartender.setup_bartender(spec=spec, cli_args=vars(args))

    bartender.logger.info("Hi, what can I get you to drink?")
    bartender.application.start()

    # You may be wondering why we don't just call bartender.application.join(), if we do
    # that, we never yield to the signal handler and thus the application cannot be stopped.
    # So, we enter a never-ending loop so that someone can set bartender.application.stopped
    # to True and we can exit out.
    while not bartender.application.stopped() and bartender.application.isAlive():
        bartender.application.join(1)
    bartender.logger.info("Don't forget to drive safe!")


if __name__ == '__main__':
    main()
