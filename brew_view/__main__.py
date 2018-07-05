#!/usr/bin/env python

import signal
import sys
from argparse import ArgumentParser

from prometheus_client import start_http_server
from yapconf import YapconfSpec

import bg_utils
import brew_view
from brew_view.specification import SPECIFICATION, get_default_logging_config
from brewtils.models import Event, Events


def signal_handler(signal_number, stack_frame):
    brew_view.logger.info("Received a shutdown request.")
    brew_view.application.add_callback_from_signal(shutdown)


def shutdown():
    # Stop the server so we don't process any more requests
    brew_view.logger.info("Stopping server.")
    brew_view.server.stop()

    # Shutdown everything short of the event loop
    # (we need the event loop to publish the shutdown event)
    brew_view.shutdown()

    # Publish shutdown notification
    brew_view.event_publishers.publish_event(Event(name=Events.BREWVIEW_STOPPED.name))

    def do_stop(*_):
        brew_view.application.stop()
        brew_view.logger.info("Application has stopped. Just waiting for start() to return.")

    # This is ... not great. Ideally we'd call shutdown() on event_publishers and it would be
    # invoked on each of them. That's causing issues because we currently don't make a distinction
    # between async an sync publishers, so for now just wait on the publisher we really care about
    if 'pika' in brew_view.event_publishers:
        brew_view.application.add_future(brew_view.event_publishers['pika'].shutdown(), do_stop)
    else:
        brew_view.application.add_callback(do_stop)


def generate_logging_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix="BG_")
    bg_utils.generate_logging_config_file(spec, get_default_logging_config, sys.argv[1:])


def generate_config():
    spec = YapconfSpec(SPECIFICATION, env_prefix='BG_')
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

    brew_view.setup_brew_view(spec, vars(args))
    brew_view.logger.debug("Application set up successfully.")

    brew_view.logger.debug("Publishing application startup event.")
    brew_view.event_publishers.publish_event(Event(name=Events.BREWVIEW_STARTED.name))

    brew_view.logger.info("Starting up the application.")
    brew_view.logger.info('Starting up metrics server on: %d' % brew_view.config.metrics.port)
    start_http_server(brew_view.config.metrics.port)

    brew_view.scheduler.start()

    brew_view.logger.info(
        'Starting up HTTP server on: %s:%d' %
        (brew_view.config.web.host, brew_view.config.web.port)
    )
    brew_view.application.start()

    brew_view.logger.info("Application is shut down.")


if __name__ == '__main__':
    main()
