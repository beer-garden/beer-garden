#!/usr/bin/env python

import signal
import sys
from argparse import ArgumentParser
from functools import partial

from yapconf import YapconfSpec

import beer_garden
import beer_garden.bg_utils
from beer_garden import progressive_backoff
from beer_garden.specification import SPECIFICATION, get_default_logging_config
from beer_garden.bg_utils.mongo import setup_database


def signal_handler(signal_number, stack_frame):
    beer_garden.logger.info("Last call! Looks like we gotta shut down.")
    beer_garden.application.stop()

    beer_garden.logger.info(
        "Closing time! You don't have to go home, but you can't stay here."
    )
    if beer_garden.application.is_alive():
        beer_garden.application.join()

    beer_garden.logger.info(
        "Looks like the Application is shut down. Have a good night!"
    )


def generate_logging_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    beer_garden.bg_utils.generate_logging_config_file(
        spec, get_default_logging_config, sys.argv[1:]
    )


def generate_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    beer_garden.bg_utils.generate_config_file(spec, sys.argv[1:])


def migrate_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    beer_garden.bg_utils.update_config_file(spec, sys.argv[1:])


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    parser = ArgumentParser()
    spec.add_arguments(parser)
    args = parser.parse_args(sys.argv[1:])

    beer_garden.setup_bartender(spec=spec, cli_args=vars(args))

    # Ensure we have a mongo connection
    progressive_backoff(
        partial(setup_database, beer_garden.config),
        beer_garden.application,
        "Unable to connect to mongo, is it started?",
    )

    # Ensure we have message queue connections
    progressive_backoff(
        beer_garden.application.clients["pika"].is_alive,
        beer_garden.application,
        "Unable to connect to rabbitmq, is it started?",
    )
    progressive_backoff(
        beer_garden.application.clients["pyrabbit"].is_alive,
        beer_garden.application,
        "Unable to connect to rabbitmq admin interface. "
        "Is the management plugin enabled?",
    )

    # Since we wait for RabbitMQ we could already be shutting down
    # In that case we don't want to start
    if not beer_garden.application.stopped():
        beer_garden.logger.info("Hi, what can I get you to drink?")
        beer_garden.application.start()

        beer_garden.logger.info("Let me know if you need anything else!")

        # You may be wondering why we don't just call beer_garden.application.join() or .wait().
        # Well, you're in luck because I'm going to tell you why. Either of these methods
        # cause the main python thread to lock out our signal handler, which means we cannot
        # shut down gracefully in some circumstances. So instead we simply use pause() to wait
        # for a signal to be sent to us. If you choose to change this please test thoroughly
        # when deployed via system packages (apt/yum) as well as python packages and docker.
        # Thanks!
        signal.pause()

    beer_garden.logger.info("Don't forget to drive safe!")


if __name__ == "__main__":
    main()
