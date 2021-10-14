# -*- coding: utf-8 -*-
"""Beer Garden Application

This is the core library for Beer-Garden. Anything that is spawned by the Main Process
in Beer-Garden will be initialized within this class.
"""
import logging
import signal
from datetime import timedelta
from functools import partial
from multiprocessing.managers import BaseManager
from typing import Callable

from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor

# from apscheduler.schedulers.background import BackgroundScheduler
from brewtils import EasyClient
from brewtils.models import Event, Events
from brewtils.stoppable_thread import StoppableThread
from pytz import utc

import beer_garden.api
import beer_garden.api.entry_point
import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.events
import beer_garden.garden
import beer_garden.local_plugins.manager
import beer_garden.namespace
import beer_garden.queue.api as queue
import beer_garden.router
from beer_garden.events.handlers import garden_callbacks
from beer_garden.events.parent_procesors import HttpParentUpdater
from beer_garden.events.processors import FanoutProcessor, QueueListener
from beer_garden.local_plugins.manager import PluginManager
from beer_garden.log import load_plugin_log_config
from beer_garden.metrics import PrometheusServer
from beer_garden.monitor import MonitorFile
from beer_garden.plugin import StatusMonitor
from beer_garden.scheduler import MixedScheduler


class Application(StoppableThread):
    """Main Beer-garden application

    This class is basically a wrapper around the various singletons that need to exist
    in order for Beer-garden to function.

    """

    request_validator = None
    scheduler = None
    clients = None
    helper_threads = None
    entry_manager = None
    mp_manager = None
    plugin_log_config_observer: MonitorFile = None
    plugin_local_log_config_observer: MonitorFile = None

    def __init__(self):
        super(Application, self).__init__(
            name="Application", logger=logging.getLogger(__name__)
        )

        self.initialize()

    def initialize(self):
        """Actually construct all the various component pieces"""

        self.scheduler = self._setup_scheduler()

        load_plugin_log_config()

        plugin_config = config.get("plugin")
        self.helper_threads = [
            HelperThread(
                StatusMonitor,
                timeout_seconds=plugin_config.status_timeout,
                heartbeat_interval=plugin_config.status_heartbeat,
            )
        ]

        # Only want to run the MongoPruner if it would do anything
        tasks, run_every = db.prune_tasks(**config.get("db.ttl"))
        if run_every:
            self.helper_threads.append(
                HelperThread(
                    db.get_pruner(), tasks=tasks, run_every=timedelta(minutes=run_every)
                )
            )

        metrics_config = config.get("metrics")
        if metrics_config.prometheus.enabled:
            self.helper_threads.append(
                HelperThread(
                    PrometheusServer,
                    metrics_config.prometheus.host,
                    metrics_config.prometheus.port,
                )
            )

        beer_garden.router.forward_processor = QueueListener(
            action=beer_garden.router.forward, name="forwarder"
        )

        self.mp_manager = self._setup_multiprocessing_manager()

        beer_garden.local_plugins.manager.lpm_proxy = self.mp_manager.PluginManager()

        self.entry_manager = beer_garden.api.entry_point.Manager()

        beer_garden.events.manager = self._setup_events_manager()

        file_event = Event(name=Events.PLUGIN_LOGGER_FILE_CHANGE.name)
        self.plugin_log_config_observer = MonitorFile(
            path=config.get("plugin.logging.config_file"),
            create_event=file_event,
            modify_event=file_event,
        )
        self.plugin_local_log_config_observer = MonitorFile(
            path=config.get("plugin.local.logging.config_file"),
            create_event=file_event,
            modify_event=file_event,
        )

    def run(self):
        """Before setting up Beer-Garden, ensures that required services are running"""
        if not self._verify_db_connection():
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

    @staticmethod
    def handle_event(event):
        """Handle any events the application cares about"""
        # Only care about local garden
        if event.garden == beer_garden.config.get("garden.name"):
            # Start local plugins after the HTTP entry point comes up
            if (
                event.name == Events.ENTRY_STARTED.name
                and event.metadata["entry_point_type"] == "HTTP"
            ):
                beer_garden.local_plugins.manager.rescan()

    def _progressive_backoff(self, func: Callable, failure_message: str):
        """Execute a function until it returns truthy, increasing wait time each attempt

        Time between execution attempts starts at 0.1 seconds and doubles each attempt,
        up to a maximum of 30 seconds.

        Args:
            func: The function that is being executed
            failure_message: Warning message logged if func returns falsey

        Returns:

        """
        wait_time = 0.1
        while not self.stopped() and not func():
            self.logger.warning(failure_message)
            self.logger.warning("Waiting %.1f seconds before next attempt", wait_time)

            self.wait(wait_time)
            wait_time = min(wait_time * 2, 30)

        return not self.stopped()

    def _verify_db_connection(self):
        """Verify that that the application can connect to a database

        Returns:
            True: the verification was successful
            False: the app was stopped before a connection could be verified
        """
        self.logger.debug("Verifying database connection...")
        return self._progressive_backoff(
            partial(db.check_connection, config.get("db")),
            "Unable to connect to database, is it started?",
        )

    def _verify_message_queue_connection(self):
        """Verify that that the application can connect to the message queue

        Returns:
            True: the verification was successful
            False: the app was stopped before a connection could be verified
        """
        self.logger.debug("Verifying message queue connection...")
        queue.create_clients(config.get("mq"))

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
        """Initializes core requirements for Application"""
        self.logger.debug("Starting Application...")

        self.logger.debug("Starting event manager...")
        beer_garden.events.manager.start()

        self.logger.debug("Setting up database...")
        db.create_connection(db_config=config.get("db"))
        db.initial_setup(config.get("auth.guest_login_enabled"))

        self.logger.debug("Setting up message queues...")
        queue.initial_setup()

        self.logger.debug("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.debug("Setting up garden routing...")
        beer_garden.router.setup_routing()

        self.logger.debug("Starting forwarding processor...")
        beer_garden.router.forward_processor.start()

        self.logger.debug("Creating and starting entry points...")
        self.entry_manager.create_all()
        self.entry_manager.start()

        self.logger.debug("Starting local plugin process monitoring...")
        beer_garden.local_plugins.manager.lpm_proxy.start()

        self.logger.debug("Starting scheduler")
        self.scheduler.start()

        self.logger.debug("Publishing startup sync")
        beer_garden.garden.publish_garden()

        self.logger.debug("Starting plugin log config file monitors")
        if config.get("plugin.logging.config_file"):
            self.plugin_log_config_observer.start()
        if config.get("plugin.local.logging.config_file"):
            self.plugin_local_log_config_observer.start()

        self.logger.debug("Loading jobs from database")
        self.scheduler.initialize_from_db()

        self.logger.info("All set! Let me know if you need anything else!")

    def _shutdown(self):
        """Shutdown core requirements for Application"""
        self.logger.info(
            "Closing time! You don't have to go home, but you can't stay here."
        )

        self.logger.debug("Publishing shutdown sync")
        beer_garden.garden.publish_garden(status="STOPPED")

        if self.scheduler.running:
            self.logger.debug("Pausing scheduler - no more jobs will be run")
            self.scheduler.pause()

        self.logger.debug("Stopping plugin log config file monitors")
        self.plugin_log_config_observer.stop()
        self.plugin_local_log_config_observer.stop()

        self.logger.debug("Stopping forwarding processor...")
        beer_garden.router.forward_processor.stop()

        self.logger.debug("Stopping helper threads")
        for helper_thread in reversed(self.helper_threads):
            helper_thread.stop()

        if self.scheduler.running:
            self.logger.debug("Shutting down scheduler")
            self.scheduler.shutdown(wait=False)

        self.logger.debug("Stopping local plugin process monitoring")
        beer_garden.local_plugins.manager.lpm_proxy.stop()

        self.logger.debug("Stopping local plugins")
        beer_garden.local_plugins.manager.lpm_proxy.stop_all()

        self.logger.debug("Stopping entry points")
        self.entry_manager.stop()

        self.logger.debug("Stopping event manager")
        beer_garden.events.manager.stop()

        self.logger.info("Successfully shut down Beer-garden")

    def _setup_events_manager(self):
        """Set up the event manager for the Main Processor"""
        event_manager = FanoutProcessor(name="event manager")

        # Forward all events down into the entry points
        event_manager.register(self.entry_manager, manage=False)

        # Register the callback processor
        event_manager.register(QueueListener(action=garden_callbacks, name="callbacks"))

        # Set up parent connection
        cfg = config.get("parent.http")
        if cfg.enabled:

            def reconnect_action():
                beer_garden.garden.publish_garden(status="RUNNING")

            easy_client = EasyClient(
                bg_host=cfg.host,
                bg_port=cfg.port,
                bg_url_prefix=cfg.url_prefix,
                access_token=cfg.access_token,
                api_version=cfg.api_version,
                client_timeout=cfg.client_timeout,
                password=cfg.password,
                refresh_token=cfg.password,
                username=cfg.username,
                ssl_enabled=cfg.ssl.enabled,
                ca_cert=cfg.ssl.ca_cert,
                ca_verify=cfg.ssl.ca_verify,
                client_cert=cfg.ssl.client_cert,
                client_key=cfg.ssl.client_key,
            )

            event_manager.register(
                HttpParentUpdater(
                    easy_client=easy_client,
                    black_list=config.get("parent.skip_events"),
                    reconnect_action=reconnect_action,
                )
            )

        return event_manager

    @staticmethod
    def _setup_scheduler():
        """Initializes scheduled jobs stored in the database"""
        job_stores = {"beer_garden": db.get_job_store()}
        scheduler_config = config.get("scheduler")
        executors = {"default": APThreadPoolExecutor(scheduler_config.max_workers)}
        job_defaults = scheduler_config.job_defaults.to_dict()

        ap_config = {
            "jobstores": job_stores,
            "executors": executors,
            "job_defaults": job_defaults,
            "timezone": utc,
        }

        # return BackgroundScheduler(
        #     jobstores=job_stores,
        #     executors=executors,
        #     job_defaults=job_defaults,
        #     timezone=utc,
        # )

        return MixedScheduler(interval_config=ap_config)

    @staticmethod
    def _setup_multiprocessing_manager():
        BaseManager.register(
            "PluginManager",
            callable=partial(
                PluginManager,
                plugin_dir=config.get("plugin.local.directory"),
                log_dir=config.get("plugin.local.log_directory"),
                connection_info=config.get("entry.http"),
                username=config.get("plugin.local.auth.username"),
                password=config.get("plugin.local.auth.password"),
            ),
        )

        def initializer():
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)

        data_manager = BaseManager()
        data_manager.start(initializer=initializer)

        return data_manager


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
        if not self.thread:
            return

        if not self.thread.is_alive():
            self.logger.warning(
                "Uh-oh. Looks like a bad shutdown - the %s was already stopped",
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
