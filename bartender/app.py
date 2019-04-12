from __future__ import division

import logging
from datetime import timedelta
from functools import partial

import time
from mongoengine import Q
from requests.exceptions import RequestException

import bartender
import bg_utils
from bartender.local_plugins.loader import LocalPluginLoader
from bartender.local_plugins.manager import LocalPluginsManager
from bartender.local_plugins.monitor import LocalPluginMonitor
from bartender.local_plugins.registry import LocalPluginRegistry
from bartender.local_plugins.validator import LocalPluginValidator
from bartender.mongo_pruner import MongoPruner
from bartender.monitor import PluginStatusMonitor
from bartender.pika import PikaClient
from bartender.pyrabbit import PyrabbitClient
from bartender.request_validator import RequestValidator
from bartender.thrift.handler import BartenderHandler
from bartender.thrift.server import make_server
from bg_utils.mongo.models import Event, Request
from brewtils.models import Events
from brewtils.stoppable_thread import StoppableThread


class BartenderApp(StoppableThread):
    """Main Application that Runs the Beergarden Backend."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.request_validator = RequestValidator()
        self.plugin_registry = LocalPluginRegistry()
        self.plugin_validator = LocalPluginValidator()

        self.plugin_loader = LocalPluginLoader(
            validator=self.plugin_validator, registry=self.plugin_registry
        )

        self.clients = {
            "pika": PikaClient(
                host=bartender.config.amq.host,
                port=bartender.config.amq.connections.message.port,
                ssl=bartender.config.amq.connections.message.ssl,
                user=bartender.config.amq.connections.admin.user,
                password=bartender.config.amq.connections.admin.password,
                virtual_host=bartender.config.amq.virtual_host,
                connection_attempts=bartender.config.amq.connection_attempts,
                blocked_connection_timeout=bartender.config.amq.blocked_connection_timeout,
                exchange=bartender.config.amq.exchange,
            ),
            "pyrabbit": PyrabbitClient(
                host=bartender.config.amq.host,
                virtual_host=bartender.config.amq.virtual_host,
                **bartender.config.amq.connections.admin
            ),
            "public": PikaClient(
                host=bartender.config.publish_hostname,
                virtual_host=bartender.config.amq.virtual_host,
                **bartender.config.amq.connections.message
            ),
        }

        self.plugin_manager = LocalPluginsManager(
            loader=self.plugin_loader,
            validator=self.plugin_validator,
            registry=self.plugin_registry,
            clients=self.clients,
        )

        self.handler = BartenderHandler(
            registry=self.plugin_registry,
            clients=self.clients,
            plugin_manager=self.plugin_manager,
            request_validator=self.request_validator,
        )

        self.helper_threads = [
            HelperThread(
                make_server,
                service=bg_utils.bg_thrift.BartenderBackend,
                handler=self.handler,
                host=bartender.config.thrift.host,
                port=bartender.config.thrift.port,
            ),
            HelperThread(
                LocalPluginMonitor,
                plugin_manager=self.plugin_manager,
                registry=self.plugin_registry,
            ),
            HelperThread(
                PluginStatusMonitor,
                self.clients,
                timeout_seconds=bartender.config.plugin.status_timeout,
                heartbeat_interval=bartender.config.plugin.status_heartbeat,
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

        self.logger.info("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.info("Loading all local plugins...")
        self.plugin_loader.load_plugins()

        self.logger.info("Starting all local plugins...")
        self.plugin_manager.start_all_plugins()

        try:
            bartender.bv_client.publish_event(name=Events.BARTENDER_STARTED.name)
        except RequestException:
            self.logger.warning("Unable to publish startup notification")

        self.logger.info("Bartender started")

    def _shutdown(self):
        self.logger.info("Shutting down Bartender...")

        self.plugin_manager.stop_all_plugins()

        self.logger.info("Stopping helper threads...")
        for helper_thread in reversed(self.helper_threads):
            helper_thread.stop()

        try:
            bartender.bv_client.publish_event(name=Events.BARTENDER_STOPPED.name)
        except RequestException:
            self.logger.warning("Unable to publish shutdown notification")

        self.logger.info("Successfully shut down Bartender")

    @staticmethod
    def _setup_pruning_tasks():

        prune_tasks = []
        if bartender.config.db.ttl.info > 0:
            prune_tasks.append(
                {
                    "collection": Request,
                    "field": "created_at",
                    "delete_after": timedelta(minutes=bartender.config.db.ttl.info),
                    "additional_query": (
                        Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                    )
                    & Q(has_parent=False)
                    & Q(command_type="INFO"),
                }
            )

        if bartender.config.db.ttl.action > 0:
            prune_tasks.append(
                {
                    "collection": Request,
                    "field": "created_at",
                    "delete_after": timedelta(minutes=bartender.config.db.ttl.action),
                    "additional_query": (
                        Q(status="SUCCESS") | Q(status="CANCELED") | Q(status="ERROR")
                    )
                    & Q(has_parent=False)
                    & Q(command_type="ACTION"),
                }
            )

        if bartender.config.db.ttl.event > 0:
            prune_tasks.append(
                {
                    "collection": Event,
                    "field": "timestamp",
                    "delete_after": timedelta(minutes=bartender.config.db.ttl.event),
                }
            )

        # Look at the various TTLs to determine how often to run the MongoPruner
        real_ttls = [x for x in bartender.config.db.ttl.values() if x > 0]
        run_every = min(real_ttls) / 2 if real_ttls else None

        return prune_tasks, run_every


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
