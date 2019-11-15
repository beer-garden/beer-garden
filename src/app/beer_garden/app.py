# -*- coding: utf-8 -*-
import logging
import multiprocessing
from datetime import timedelta
from functools import partial

import brewtils.models
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from brewtils.models import Events
from brewtils.pika import TransientPikaClient
from brewtils.rest.easy_client import EasyClient
from brewtils.stoppable_thread import StoppableThread
from pytz import utc
from requests.exceptions import RequestException

import beer_garden
import beer_garden.api
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.api.entry_point import EntryPoint
from beer_garden.bg_utils.event_publisher import EventPublishers, EventPublisher
from beer_garden.bg_utils.publishers import MongoPublisher
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
    event_publishers = None
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
        self.event_publishers = EventPublishers()

        load_plugin_log_config()

        self.plugin_manager = LocalPluginsManager(
            shutdown_timeout=beer_garden.config.get("plugin.local.timeout.shutdown")
        )

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

    def _startup(self):
        self.logger.debug("Starting Application...")

        self.logger.debug("Setting up database...")
        self._setup_database()

        self.logger.debug("Setting up queues...")
        self._setup_queues()

        self.logger.debug("Starting event publishers")
        self.event_publishers = self._setup_event_publishers()
        # self.event_publishers = self._setup_event_publishers(client_ssl)

        self.logger.debug("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.info("Starting log reader...")
        self.log_reader.start()

        self.logger.debug("Starting entry points...")
        for entry_point in self.entry_points:
            entry_point.start(context=self.context, log_queue=self.log_queue)

        self.logger.debug("Loading all local plugins...")
        LocalPluginLoader.instance().load_plugins()

        self.logger.debug("Starting all local plugins...")
        self.plugin_manager.start_all_plugins()

        self.logger.debug("Starting scheduler")
        self.scheduler.start()

        try:
            self.event_publishers.publish_event(
                brewtils.models.Event(name=Events.BARTENDER_STARTED.name)
            )
            # beer_garden.bv_client.publish_event(name=Events.BARTENDER_STARTED.name)
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
            self.event_publishers.publish_event(
                brewtils.models.Event(name=Events.BARTENDER_STOPPED.name)
            )
            # beer_garden.bv_client.publish_event(name=Events.BARTENDER_STOPPED.name)
        except RequestException:
            self.logger.warning("Unable to publish shutdown notification")

        self.logger.debug("Stopping entry points")
        for entry_point in self.entry_points:
            entry_point.stop(timeout=10)

        self.logger.info("Stopping log reader")
        self.log_reader.stop()

        self.logger.info("Successfully shut down Beer-garden")

    def _setup_database(self):
        """Startup tasks related to the database

        This will:
          - ensure a connection to the database (using a connection with short timeouts)
          - create the actual connection to the database
          - ensure the database is in a good state
        """
        self._progressive_backoff(
            partial(db.check_connection, beer_garden.config.get("db")),
            "Unable to connect to mongo, is it started?",
        )
        db.create_connection(db_config=beer_garden.config.get("db"))
        db.initial_setup(beer_garden.config.get("auth.guest_login_enabled"))

    def _setup_queues(self):
        """Startup tasks related to the message queues

        This will:
          - create the message queue clients
          - make sure that all clients have active connections
          - ensure the broker and queues are in a good state
        """
        queue.create_clients(beer_garden.config.get("amq"))

        self._progressive_backoff(
            partial(queue.check_connection, "pika"),
            "Unable to connect to rabbitmq, is it started?",
        )
        self._progressive_backoff(
            partial(queue.check_connection, "pyrabbit"),
            "Unable to connect to rabbitmq admin interface. "
            "Is the management plugin enabled?",
        )

        queue.initial_setup()

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

    # def _setup_event_publishers(self, ssl_context):
    def _setup_event_publishers(self):
        # Create the collection of event publishers and add concrete publishers
        pubs = EventPublishers(
            # {
            #     "webhook": WebhookPublisher(ssl_context=ssl_context),
            # }
        )

        event_config = beer_garden.config.get("event")
        if event_config.mongo.enable:
            try:
                pubs["mongo"] = MongoPublisher()
            except Exception as ex:
                self.logger.warning("Error starting Mongo event publisher: %s", ex)

        if event_config.amq.enable:
            try:
                amq_config = beer_garden.config.get("amq")

                pika_params = {
                    "host": amq_config.host,
                    "port": amq_config.connections.message.port,
                    "ssl": amq_config.connections.message.ssl,
                    "user": amq_config.connections.admin.user,
                    "password": amq_config.connections.admin.password,
                    "exchange": event_config.amq.exchange,
                    "virtual_host": event_config.amq.virtual_host,
                    "connection_attempts": amq_config.connection_attempts,
                }

                # Make sure the exchange exists
                TransientPikaClient(**pika_params).declare_exchange()

                # pubs["pika"] = TornadoPikaPublisher(
                #     shutdown_timeout=beer_garden.config.shutdown_timeout, **pika_params
                # )
            except Exception as ex:
                self.logger.exception("Error starting RabbitMQ event publisher: %s", ex)

        if event_config.brew_view.enable:

            class BrewViewPublisher(EventPublisher):
                def __init__(self, config):
                    self._ez_client = EasyClient(namespace="default", **config)

                def publish(self, event, **kwargs):
                    self._ez_client.publish_event(event)

                def _event_serialize(self, event, **kwargs):
                    return event

            pubs["brewview"] = BrewViewPublisher(event_config.brew_view)

        # Metadata functions - additional metadata to be included with each event
        # pubs.metadata_funcs["public_url"] = lambda: public_url

        return pubs


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
