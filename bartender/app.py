import logging
import time
from datetime import timedelta
from functools import partial

from mongoengine import Q

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
from bg_utils.models import Event, Request
from bg_utils.pika import ClientBase
from brewtils.models import Events
from brewtils.stoppable_thread import StoppableThread


class BartenderApp(StoppableThread):
    """Main Application that Runs the Beergarden Backend."""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

        self.request_validator = RequestValidator(config)
        self.plugin_registry = LocalPluginRegistry()
        self.plugin_validator = LocalPluginValidator()

        self.plugin_loader = LocalPluginLoader(path_to_plugins=config.plugin_directory,
                                               validator=self.plugin_validator,
                                               registry=self.plugin_registry,
                                               web_host=config.web_host,
                                               web_port=config.web_port,
                                               ssl_enabled=config.ssl_enabled,
                                               db_host=config.db_host,
                                               db_name=config.db_name,
                                               db_port=config.db_port,
                                               plugin_log_directory=config.plugin_log_directory,
                                               url_prefix=config.url_prefix,
                                               ca_verify=config.ca_verify,
                                               ca_cert=config.ca_cert)

        self.clients = {
            'pika': PikaClient(host=config.amq_host, port=config.amq_port,
                               user=config.amq_admin_user,
                               password=config.amq_admin_password,
                               virtual_host=config.amq_virtual_host,
                               connection_attempts=config.amq_connection_attempts,
                               exchange=config.amq_exchange),
            'pyrabbit': PyrabbitClient(host=config.amq_admin_host, port=config.amq_admin_port,
                                       user=config.amq_admin_user,
                                       password=config.amq_admin_password,
                                       virtual_host=config.amq_virtual_host),
            'public': ClientBase(host=config.amq_publish_host, port=config.amq_port,
                                 user=config.amq_user, password=config.amq_password,
                                 virtual_host=config.amq_virtual_host)
        }

        self.plugin_manager = LocalPluginsManager(
            loader=self.plugin_loader, validator=self.plugin_validator,
            registry=self.plugin_registry, clients=self.clients,
            plugin_startup_timeout=config.plugin_startup_timeout,
            plugin_shutdown_timeout=config.plugin_shutdown_timeout)

        self.handler = BartenderHandler(registry=self.plugin_registry, clients=self.clients,
                                        plugin_manager=self.plugin_manager,
                                        request_validator=self.request_validator)

        self.helper_threads = [

            HelperThread(make_server, service=bg_utils.bg_thrift.BartenderBackend,
                         handler=self.handler, host=config.thrift_host, port=config.thrift_port),

            HelperThread(LocalPluginMonitor, plugin_manager=self.plugin_manager,
                         registry=self.plugin_registry),

            HelperThread(PluginStatusMonitor, self.clients,
                         timeout_seconds=config.plugin_status_timeout,
                         heartbeat_interval=config.plugin_status_heartbeat)
        ]

        # Only want to run the MongoPruner if it would do anything
        tasks, run_every = self._setup_pruning_tasks(config)
        if run_every:
            self.helper_threads.append(HelperThread(MongoPruner, tasks=tasks,
                                                    run_every=timedelta(minutes=run_every)))

        super(BartenderApp, self).__init__(logger=self.logger, name="BartenderApp")

    def run(self):
        self._startup()

        while not self.stopped():
            for helper_thread in self.helper_threads:
                if not helper_thread.thread.isAlive():
                    self.logger.warning("%s is dead, restarting" % helper_thread.display_name)
                    helper_thread.start()

            time.sleep(0.1)

        self._shutdown()

    def _startup(self):
        self.logger.info("Starting Bartender...")

        self.logger.info("Verifying message virtual host...")
        self.clients['pyrabbit'].verify_virtual_host()

        self.logger.info("Declaring message exchange...")
        self.clients['pika'].declare_exchange()

        self.logger.info("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.info("Loading all local plugins...")
        self.plugin_loader.load_plugins()

        self.logger.info("Starting all local plugins...")
        self.plugin_manager.start_all_plugins()

        bartender.bv_client.publish_event(name=Events.BARTENDER_STARTED.name)
        self.logger.info("Bartender started")

    def _shutdown(self):
        self.logger.info("Shutting down Bartender...")

        self.plugin_manager.stop_all_plugins()

        self.logger.info("Stopping helper threads...")
        for helper_thread in reversed(self.helper_threads):
            helper_thread.stop()

        bartender.bv_client.publish_event(name=Events.BARTENDER_STOPPED.name)
        self.logger.info("Successfully shut down Bartender")

    @staticmethod
    def _setup_pruning_tasks(config):

        prune_tasks = []
        if config.info_request_ttl > 0:
            prune_tasks.append({
                'collection': Request, 'field': 'created_at',
                'delete_after': timedelta(minutes=config.info_request_ttl),
                'additional_query':
                    (Q(status="SUCCESS") |
                     Q(status='CANCELED') |
                     Q(status='ERROR')) & Q(command_type='INFO')})

        if config.action_request_ttl > 0:
            prune_tasks.append({
                'collection': Request, 'field': 'created_at',
                'delete_after': timedelta(minutes=config.action_request_ttl),
                'additional_query':
                    (Q(status="SUCCESS") |
                     Q(status='CANCELED') |
                     Q(status='ERROR')) & Q(command_type='ACTION')})

        if config.event_mongo_ttl > 0:
            prune_tasks.append({'collection': Event, 'field': 'timestamp',
                                'delete_after': timedelta(minutes=config.event_mongo_ttl)})

        # Look at the various TTLs to determine how often to run the MongoPruner
        real_ttls = [x for x in
                     (config.info_request_ttl, config.action_request_ttl, config.event_mongo_ttl)
                     if x > 0]
        run_every = min(real_ttls) // 2 if real_ttls else None

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
            self.logger.warning("Uh-oh. Looks like a bad shutdown - the %s "
                                "was already stopped", self.display_name)
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
        return getattr(self.thread, 'display_name', str(self.thread))
