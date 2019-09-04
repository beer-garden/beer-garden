#!/usr/bin/env python

import signal
import sys

import beer_garden.bg_utils
import beer_garden.brew_view


def signal_handler(signal_number, stack_frame):
    beer_garden.brew_view.logger.info("Received a shutdown request.")
    beer_garden.brew_view.io_loop.add_callback_from_signal(
        beer_garden.brew_view.shutdown
    )


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Logging isn't set up until after this...
    beer_garden.brew_view.setup(sys.argv[1:])

    # Schedule things to happen after the ioloop comes up
    beer_garden.brew_view.io_loop.add_callback(beer_garden.brew_view.startup)

    beer_garden.brew_view.logger.info("Starting IO loop")
    beer_garden.brew_view.io_loop.start()

    beer_garden.brew_view.logger.info("Application is shut down. Goodbye!")


if __name__ == "__main__":
    main()
