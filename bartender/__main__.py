#!/usr/bin/env python

import signal
import sys
from argparse import ArgumentParser
from functools import partial

from yapconf import YapconfSpec

import bartender
import bg_utils
from bartender import progressive_backoff
from bartender.specification import SPECIFICATION, get_default_logging_config
from bg_utils.mongo import setup_database


def signal_handler(signal_number, stack_frame):
    bartender.logger.info("Last call! Looks like we gotta shut down.")
    bartender.application.stop()

    bartender.logger.info(
        "Closing time! You don't have to go home, but you can't stay here."
    )
    if bartender.application.is_alive():
        bartender.application.join()

    bartender.logger.info("Looks like the Application is shut down. Have a good night!")


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

    bartender.setup_bartender(spec=spec, cli_args=vars(args))

    # Ensure we have a brew-view connection
    progressive_backoff(
        partial(bartender.bv_client.can_connect, timeout=5),
        bartender.application,
        "Unable to connect to brew-view, is it started?",
    )

    # Ensure we have a mongo connection
    progressive_backoff(
        partial(setup_database, bartender.config),
        bartender.application,
        "Unable to connect to mongo, is it started?",
    )

    # Ensure we have message queue connections
    progressive_backoff(
        bartender.application.clients["pika"].is_alive,
        bartender.application,
        "Unable to connect to rabbitmq, is it started?",
    )
    progressive_backoff(
        bartender.application.clients["pyrabbit"].is_alive,
        bartender.application,
        "Unable to connect to rabbitmq admin interface. "
        "Is the management plugin enabled?",
    )

    # Since we wait for RabbitMQ and brew-view we could already be shutting down
    # In that case we don't want to start
    if not bartender.application.stopped():
        # Make sure that the bartender user has admin permissions
        bartender.ensure_admin()

        bartender.logger.info("Hi, what can I get you to drink?")
        bartender.application.start()

        bartender.logger.info("Let me know if you need anything else!")

        # You may be wondering why we don't just call bartender.application.join() or .wait().
        # Well, you're in luck because I'm going to tell you why. Either of these methods
        # cause the main python thread to lock out our signal handler, which means we cannot
        # shut down gracefully in some circumstances. So instead we simply use pause() to wait
        # for a signal to be sent to us. If you choose to change this please test thoroughly
        # when deployed via system packages (apt/yum) as well as python packages and docker.
        # Thanks!
        signal.pause()

    bartender.logger.info("Don't forget to drive safe!")


if __name__ == "__main__":
    main()
