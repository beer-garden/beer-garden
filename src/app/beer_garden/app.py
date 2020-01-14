# -*- coding: utf-8 -*-
import logging
import multiprocessing
from datetime import timedelta
from functools import partial

import brewtils.models
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from beer_garden.events.events_manager import EventsManager
from beer_garden.events.parent_http_processor import ParentHttpProcessor
from brewtils.models import Events
from brewtils.stoppable_thread import StoppableThread
from pytz import utc
from requests.exceptions import RequestException

import beer_garden
import beer_garden.api
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.api.entry_point import EntryPoint
from beer_garden.db.mongo.jobstore import MongoJobStore
from beer_garden.db.mongo.pruner import MongoPruner
from beer_garden.local_plugins.loader import LocalPluginLoader
from beer_garden.local_plugins.manager import LocalPluginsManager
from beer_garden.local_plugins.monitor import LocalPluginMonitor
from beer_garden.log import load_plugin_log_config, EntryPointLogger
from beer_garden.metrics import PrometheusServer
from beer_garden.monitor import PluginStatusMonitor


class Application(StoppableThread):
    """Main Beer-garden application

    This class is basically a wrapper around the various singletons that need to exist
    in order for Beer-garden to function.

    """

    request_validator = None
    scheduler = None
    plugin_manager = None
    clients = None
    helper_threads = None
    context = None
    log_queue = None
    log_reader = None
    entry_points = []

    def __init__(self):
        super(Application, self).__init__(
            name="Application", logger=logging.getLogger(__name__)
        )

        self.initialize()

    def initialize(self):
        """Actually construct all the various component pieces"""
        self.scheduler = self._setup_scheduler()

        load_plugin_log_config()

        self.plugin_manager = LocalPluginsManager(
            shutdown_timeout=beer_garden.config.get("plugin.local.timeout.shutdown")
        )

        self._setup_events_manager()

        plugin_config = beer_garden.config.get("plugin")
        self.helper_threads = [
            HelperThread(LocalPluginMonitor, plugin_manager=self.plugin_manager),
            HelperThread(
                PluginStatusMonitor,
                timeout_seconds=plugin_config.status_timeout,
                heartbeat_interval=plugin_config.status_heartbeat,
            ),
        ]

        # Only want to run the MongoPruner if it would do anything
        tasks, run_every = MongoPruner.determine_tasks(
            **beer_garden.config.get("db.ttl")
        )
        if run_every:
            self.helper_threads.append(
                HelperThread(
                    MongoPruner, tasks=tasks, run_every=timedelta(minutes=run_every)
                )
            )

        metrics_config = beer_garden.config.get("metrics")
        if metrics_config.prometheus.enabled:
            self.helper_threads.append(
                HelperThread(
                    PrometheusServer,
                    metrics_config.prometheus.host,
                    metrics_config.prometheus.port,
                )
            )

        self.context = multiprocessing.get_context("spawn")
        self.log_queue = self.context.Queue()
        self.log_reader = HelperThread(EntryPointLogger, log_queue=self.log_queue)

        for entry_name, entry_value in beer_garden.config.get("entry").items():
            if entry_value.get("enable"):
                self.entry_points.append(EntryPoint.create(entry_name))

    def run(self):
        if not self._verify_mongo_connection():
            return

        if not self._verify_message_queue_connection():
            return

        self._startup()

        while not self.wait(0.1):
            for helper in self.helper_threads:
                if not helper.thread.is_alive():
                    self.logger.warning(f"{helper.display_name} is dead, restarting")
                    helper.start()

        self._shutdown()

    def _progressive_backoff(self, func, failure_message):
        wait_time = 0.1
        while not self.stopped() and not func():
            self.logger.warning(failure_message)
            self.logger.warning("Waiting %.1f seconds before next attempt", wait_time)

            self.wait(wait_time)
            wait_time = min(wait_time * 2, 30)

        return not self.stopped()

    def _verify_mongo_connection(self):
        """Verify that that the application can connect to mongo

        Returns:
            True: the verification was successful
            False: the app was stopped before a connection could be verified
        """
        self.logger.debug("Verifying mongo connection...")
        return self._progressive_backoff(
            partial(db.check_connection, beer_garden.config.get("db")),
            "Unable to connect to mongo, is it started?",
        )

    def _verify_message_queue_connection(self):
        """Verify that that the application can connect to the message queue

        Returns:
            True: the verification was successful
            False: the app was stopped before a connection could be verified
        """
        self.logger.debug("Verifying message queue connection...")
        queue.create_clients(beer_garden.config.get("amq"))

        if not self._progressive_backoff(
            partial(queue.check_connection, "pika"),
            "Unable to connect to rabbitmq, is it started?",
        ):
            return False

        return self._progressive_backoff(
            partial(queue.check_connection, "pyrabbit"),
            "Unable to connect to rabbitmq admin interface. "
            "Is the management plugin enabled?",
        )

    def _startup(self):
        self.logger.debug("Starting Application...")

        self.logger.debug("Starting event manager...")
        self.events_manager.start()

        self.logger.debug("Setting up database...")
        db.create_connection(db_config=beer_garden.config.get("db"))
        db.initial_setup(beer_garden.config.get("auth.guest_login_enabled"))

        self.logger.debug("Setting up message queues...")
        queue.initial_setup()

        self.logger.debug("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.info("Starting log reader...")
        self.log_reader.start()

        self.logger.debug("Starting entry points...")
        for entry_point in self.entry_points:
            entry_point.start(
                context=self.context,
                log_queue=self.log_queue,
                events_queue=beer_garden.events.events_manager.events_queue,
            )

        self.logger.debug("Loading all local plugins...")
        LocalPluginLoader.instance().load_plugins()

        self.logger.debug("Starting all local plugins...")
        self.plugin_manager.start_all_plugins()

        self.logger.debug("Starting scheduler")
        self.scheduler.start()

        try:
            self.events_manager.add_event(
                brewtils.models.Event(name=Events.BARTENDER_STARTED.name)
            )
        except RequestException:
            self.logger.warning("Unable to publish startup notification")

        self.logger.info("All set! Let me know if you need anything else!")

    def _shutdown(self):
        self.logger.info(
            "Closing time! You don't have to go home, but you can't stay here."
        )

        if self.scheduler.running:
            self.logger.debug("Pausing scheduler - no more jobs will be run")
            self.scheduler.pause()

        self.plugin_manager.stop_all_plugins()

        self.logger.debug("Stopping helper threads")
        for helper_thread in reversed(self.helper_threads):
            helper_thread.stop()

        if self.scheduler.running:
            self.logger.debug("Shutting down scheduler")
            self.scheduler.shutdown(wait=False)

        try:
            self.events_manager.add_event(
                brewtils.models.Event(name=Events.BARTENDER_STOPPED.name)
            )
        except RequestException:
            self.logger.warning("Unable to publish shutdown notification")

        self.logger.debug("Stopping entry points")
        for entry_point in self.entry_points:
            entry_point.stop(timeout=10)

        self.logger.info("Stopping log reader")
        self.log_reader.stop()

        self.logger.info("Stopping local events manager")
        self.events_manager.stop()

        self.logger.info("Successfully shut down Beer-garden")

    def _setup_events_manager(self):
        beer_garden.events.events_manager.establish_events_queue()

        self.events_manager = EventsManager(
            beer_garden.events.events_manager.events_queue
        )

        event_config = beer_garden.config.get("event")
        if event_config.parent.http.enable:
            self.events_manager.register_processor(
                ParentHttpProcessor(
                    event_config.parent.http, beer_garden.config.get("garden_name")
                )
            )

    @staticmethod
    def _setup_scheduler():
        job_stores = {"beer_garden": MongoJobStore()}
        scheduler_config = beer_garden.config.get("scheduler")
        executors = {"default": APThreadPoolExecutor(scheduler_config.max_workers)}
        job_defaults = scheduler_config.job_defaults.to_dict()

        return BackgroundScheduler(
            jobstores=job_stores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=utc,
        )


class HelperThread(object):
    def __init__(self, init_callable, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        self.loader_func = partial(init_callable, *args, **kwargs)
        self.thread = None

    def start(self):
        self.thread = self.loader_func()
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        # Thread was never started - nothing to do
        if not getattr(self, "thread"):
            return

        if not self.thread.is_alive():
            self.logger.warning(
                "Uh-oh. Looks like a bad shutdown - the %s " "was already stopped",
                self.display_name,
            )
        else:
            self.logger.debug("%s is being requested to stop", self.display_name)
            self.thread.stop()

            self.logger.debug("Waiting for %s to stop...", self.display_name)
            self.thread.join(2)

            if self.thread.is_alive():
                self.logger.warning("%s did not stop successfully.", self.display_name)
            else:
                self.logger.debug("%s successfully stopped", self.display_name)

    @property
    def display_name(self):
        return getattr(self.thread, "display_name", str(self.thread))
