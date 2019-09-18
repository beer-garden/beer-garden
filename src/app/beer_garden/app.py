from __future__ import division

import logging

import time
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta
from functools import partial
from mongoengine import Q
from pytz import utc
from requests.exceptions import RequestException

import beer_garden
import brewtils.models
import brewtils.thrift
from beer_garden.local_plugins.loader import LocalPluginLoader
from beer_garden.local_plugins.manager import LocalPluginsManager
from beer_garden.local_plugins.monitor import LocalPluginMonitor
from beer_garden.local_plugins.registry import LocalPluginRegistry
from beer_garden.local_plugins.validator import LocalPluginValidator
from beer_garden.log import load_plugin_log_config
from beer_garden.metrics import PrometheusServer
from beer_garden.mongo_pruner import MongoPruner
from beer_garden.monitor import PluginStatusMonitor
from beer_garden.rabbitmq import PikaClient, PyrabbitClient
from beer_garden.requests import RequestValidator
from beer_garden.scheduler import BGJobStore
from beer_garden.thrift.handler import BartenderHandler
from beer_garden.thrift.server import make_server
from beer_garden.bg_utils.event_publisher import EventPublishers, EventPublisher
from beer_garden.bg_utils.mongo.models import Event, Request
from beer_garden.bg_utils.publishers import MongoPublisher
from brewtils.models import Events
from brewtils.pika import TransientPikaClient
from brewtils.rest.easy_client import EasyClient
from brewtils.stoppable_thread import StoppableThread


class BartenderApp(StoppableThread):
    """Main Application that Runs the Beergarden Backend."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.request_validator = RequestValidator(beer_garden.config.get("validator"))
        self.plugin_registry = LocalPluginRegistry()
        self.plugin_validator = LocalPluginValidator()
        self.scheduler = self._setup_scheduler()
        self.event_publishers = EventPublishers()

        load_plugin_log_config()

        self.plugin_loader = LocalPluginLoader(
            validator=self.plugin_validator, registry=self.plugin_registry
        )

        amq_config = beer_garden.config.get("amq")
        self.clients = {
            "pika": PikaClient(
                host=amq_config.host,
                port=amq_config.connections.message.port,
                ssl=amq_config.connections.message.ssl,
                user=amq_config.connections.admin.user,
                password=amq_config.connections.admin.password,
                virtual_host=amq_config.virtual_host,
                connection_attempts=amq_config.connection_attempts,
                blocked_connection_timeout=amq_config.blocked_connection_timeout,
                exchange=amq_config.exchange,
            ),
            "pyrabbit": PyrabbitClient(
                host=amq_config.host,
                virtual_host=amq_config.virtual_host,
                admin_expires=amq_config.admin_queue_expiry,
                **amq_config.connections.admin
            ),
        }

        self.plugin_manager = LocalPluginsManager(
            loader=self.plugin_loader,
            validator=self.plugin_validator,
            registry=self.plugin_registry,
            clients=self.clients,
            shutdown_timeout=beer_garden.config.get("plugin.local.timeout.shutdown"),
        )

        self.handler = BartenderHandler()

        # TODO: The thrift portion is currently hardcoded, because it should
        # no longer be in the config. Eventually the thrift thread will be removed.
        plugin_config = beer_garden.config.get("plugin")
        self.helper_threads = [
            HelperThread(
                make_server,
                service=brewtils.thrift.bg_thrift.BartenderBackend,
                handler=self.handler,
                host="0.0.0.0",
                port=9090,
            ),
            HelperThread(
                LocalPluginMonitor,
                plugin_manager=self.plugin_manager,
                registry=self.plugin_registry,
            ),
            HelperThread(
                PluginStatusMonitor,
                self.clients,
                timeout_seconds=plugin_config.status_timeout,
                heartbeat_interval=plugin_config.status_heartbeat,
            ),
        ]

        # Only want to run the MongoPruner if it would do anything
        tasks, run_every = self._setup_pruning_tasks()
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

        super(BartenderApp, self).__init__(logger=self.logger, name="BartenderApp")

    def run(self):
        self._startup()

        while not self.stopped():
            for helper_thread in self.helper_threads:
                if not helper_thread.thread.isAlive():
                    self.logger.warning(
                        "%s is dead, restarting" % helper_thread.display_name
                    )
                    helper_thread.start()

            time.sleep(0.1)

        self._shutdown()

    def _startup(self):
        self.logger.info("Starting Bartender...")

        self.logger.info("Verifying message virtual host...")
        self.clients["pyrabbit"].verify_virtual_host()

        self.logger.info("Ensuring admin queue expiration policy...")
        self.clients["pyrabbit"].ensure_admin_expiry()

        self.logger.info("Declaring message exchange...")
        self.clients["pika"].declare_exchange()

        self.logger.info("Starting event publishers")
        self.event_publishers = self._setup_event_publishers()
        # self.event_publishers = self._setup_event_publishers(client_ssl)

        self.logger.info("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.info("Loading all local plugins...")
        self.plugin_loader.load_plugins()

        self.logger.info("Starting all local plugins...")
        self.plugin_manager.start_all_plugins()

        self.logger.info("Starting scheduler")
        self.scheduler.start()

        try:
            self.event_publishers.publish_event(
                brewtils.models.Event(name=Events.BARTENDER_STARTED.name)
            )
            # beer_garden.bv_client.publish_event(name=Events.BARTENDER_STARTED.name)
        except RequestException:
            self.logger.warning("Unable to publish startup notification")

        self.logger.info("Bartender started")

    def _shutdown(self):
        self.logger.info("Shutting down Bartender...")

        if self.scheduler.running:
            self.logger.info("Pausing scheduler - no more jobs will be run")
            self.scheduler.pause()

        self.plugin_manager.stop_all_plugins()

        self.logger.info("Stopping helper threads...")
        for helper_thread in reversed(self.helper_threads):
            helper_thread.stop()

        if self.scheduler.running:
            self.logger.info("Shutting down scheduler")
            self.scheduler.shutdown(wait=False)

        try:
            self.event_publishers.publish_event(
                brewtils.models.Event(name=Events.BARTENDER_STOPPED.name)
            )
            # beer_garden.bv_client.publish_event(name=Events.BARTENDER_STOPPED.name)
        except RequestException:
            self.logger.warning("Unable to publish shutdown notification")

        self.logger.info("Successfully shut down Bartender")

    @staticmethod
    def _setup_pruning_tasks():

        prune_tasks = []
        db_config = beer_garden.config.get("db")
        if db_config.ttl.info > 0:
            prune_tasks.append(
                {
                    "collection": Request,
                    "field": "created_at",
                    "delete_after": timedelta(minutes=db_config.ttl.info),
                    "additional_query": (
                        Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                    )
                    & Q(has_parent=False)
                    & Q(command_type="INFO"),
                }
            )

        if db_config.ttl.action > 0:
            prune_tasks.append(
                {
                    "collection": Request,
                    "field": "created_at",
                    "delete_after": timedelta(minutes=db_config.ttl.action),
                    "additional_query": (
                        Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                    )
                    & Q(has_parent=False)
                    & Q(command_type="ACTION"),
                }
            )

        if db_config.ttl.event > 0:
            prune_tasks.append(
                {
                    "collection": Event,
                    "field": "timestamp",
                    "delete_after": timedelta(minutes=db_config.ttl.event),
                }
            )

        # Look at the various TTLs to determine how often to run the MongoPruner
        real_ttls = [x for x in db_config.ttl.values() if x > 0]
        run_every = min(real_ttls) / 2 if real_ttls else None

        return prune_tasks, run_every

    @staticmethod
    def _setup_scheduler():
        job_stores = {"beer_garden": BGJobStore()}
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
        if not self.thread.isAlive():
            self.logger.warning(
                "Uh-oh. Looks like a bad shutdown - the %s " "was already stopped",
                self.display_name,
            )
        else:
            self.logger.debug("%s is being requested to stop", self.display_name)
            self.thread.stop()

            self.logger.debug("Waiting for %s to stop...", self.display_name)
            self.thread.join(2)

            if self.thread.isAlive():
                self.logger.warning("%s did not stop successfully.", self.display_name)
            else:
                self.logger.debug("%s successfully stopped", self.display_name)

    @property
    def display_name(self):
        return getattr(self.thread, "display_name", str(self.thread))
