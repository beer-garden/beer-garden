#!/usr/bin/env python

import signal
import sys
from functools import partial

import beer_garden
import beer_garden.api.brew_view
import beer_garden.api.thrift
from beer_garden import progressive_backoff
from beer_garden.bg_utils.mongo import setup_database
from beer_garden.config import generate_logging, generate, migrate

entry_point = None


def signal_handler(signal_number, stack_frame):
    beer_garden.logger.info("Last call! Looks like we gotta shut down.")
    beer_garden.application.stop()
    entry_point.stop()

    beer_garden.logger.info(
        "Closing time! You don't have to go home, but you can't stay here."
    )
    if beer_garden.application.is_alive():
        beer_garden.application.join()

    beer_garden.logger.info(
        "Looks like the Application is shut down. Have a good night!"
    )


def generate_logging_config():
    generate_logging(sys.argv[1:])


def generate_config():
    generate(sys.argv[1:])


def migrate_config():
    migrate(sys.argv[1:])


def get_entry_point():

    if beer_garden.config.get("entry.http.enable"):
        return beer_garden.api.brew_view
    elif beer_garden.config.get("entry.thrift.enable"):
        return beer_garden.api.thrift

    raise Exception("Please enable an entrypoint")


def main():
    global entry_point

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    beer_garden.setup_bartender(sys.argv[1:])

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
        # signal.pause()
        # TODO - THOROUGHLY test as requested :)
        entry_point = get_entry_point()
        entry_point.run()

    beer_garden.logger.info("Don't forget to drive safe!")


if __name__ == "__main__":
    main()
