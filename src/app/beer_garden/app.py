# -*- coding: utf-8 -*-
"""Beer Garden Application

This is the core library for Beer-Garden. Anything that is spawned by the Main Process
in Beer-Garden will be initialized within this class.
"""
import logging
import os
import signal
import traceback
from functools import partial
from multiprocessing.managers import BaseManager
from typing import Callable

from brewtils import EasyClient
from brewtils.models import Event, Events
from brewtils.stoppable_thread import StoppableThread

import beer_garden.api
import beer_garden.api.entry_point
import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.db.mongo.pruner
import beer_garden.events
import beer_garden.events.handlers
import beer_garden.garden
import beer_garden.local_plugins.manager
import beer_garden.namespace
import beer_garden.queue.api as queue
import beer_garden.router
import beer_garden.scheduler
from beer_garden.events.parent_processors import HttpParentUpdater
from beer_garden.events.processors import EventProcessor, FanoutProcessor, QueueListener
from beer_garden.local_plugins.manager import PluginManager
from beer_garden.log import load_plugin_log_config
from beer_garden.metrics import PrometheusServer, initialize_elastic_client
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
    client = None

    def __init__(self):
        super(Application, self).__init__(
            name="Application", logger=logging.getLogger(__name__)
        )

        self.initialize()

    def initialize(self):
        """Actually construct all the various component pieces"""

        initialize_elastic_client("core")

        # Setup Replication ID for environment
        beer_garden.replication.get_replication_id()

        self.scheduler = MixedScheduler()

        load_plugin_log_config()

        if config.get("auth.enabled"):
            beer_garden.user.validated_token_ttl()

        if config.get("replication.enabled"):
            import secrets

            sleep_time = secrets.randbelow(60)
            self.logger.info(
                f"Replication Enabled, Staggering Start Time by {sleep_time} Seconds..."
            )

            import time

            time.sleep(sleep_time)

        plugin_config = config.get("plugin")
        self.helper_threads = [
            HelperThread(
                StatusMonitor,
                timeout_seconds=plugin_config.status_timeout,
                heartbeat_interval=plugin_config.status_heartbeat,
            )
        ]

        metrics_config = config.get("metrics")
        if metrics_config.prometheus.enabled:
            self.helper_threads.append(
                HelperThread(
                    PrometheusServer,
                    metrics_config.prometheus.host,
                    metrics_config.prometheus.port,
                )
            )

        self.helper_threads.append(
            HelperThread(
                beer_garden.replication.PrimaryReplicationMonitor,
                10,
                30,
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

        try:
            self._startup()
        except Exception as ex:
            tbe = traceback.TracebackException.from_exception(ex)
            stack_frames = traceback.extract_stack()
            tbe.stack.extend(stack_frames)
            formatted_traceback = "".join(tbe.format())
            self.logger.error(
                "Startup Failure %s: %s"
                % (
                    str(ex),
                    formatted_traceback,
                )
            )
            self._shutdown(shutdown_failure=True)
            return

        while not self.wait(0.1):
            for helper in self.helper_threads:
                if not helper.thread.is_alive():
                    self.logger.warning(f"{helper.display_name} is dead, restarting")
                    helper.start()

            self.entry_manager.check_entry_points()
            beer_garden.local_plugins.manager.lpm_proxy.monitor()

        self._shutdown()

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

        if config.get("replication.enabled"):
            queue.create_fanout_client(config.get("mq"))

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

        self.logger.debug("Setting up database...")
        db.create_connection(db_config=config.get("db"))
        db.initial_setup()

        self.logger.debug("Starting event manager...")
        beer_garden.events.manager.start()

        self.logger.debug("Setting up message queues...")
        queue.initial_setup()

        if config.get("replication.enabled"):
            self.logger.debug("Setting up fanout message queues...")
            queue.setup_event_consumer(config.get("mq"))

        self.logger.debug("Loading child configurations...")
        beer_garden.garden.rescan()

        self.logger.debug("Setting up garden routing...")
        beer_garden.router.setup_routing()

        self.logger.debug("Loading Roles...")
        beer_garden.role.ensure_roles()

        self.logger.debug("Loading Users...")
        beer_garden.user.ensure_users()

        self.logger.debug("Starting forwarding processor...")
        beer_garden.router.forward_processor.start()

        self.logger.debug("Creating and starting entry points...")
        self.entry_manager.create_all()
        self.entry_manager.start()

        self.logger.debug("Starting local plugin process monitoring...")
        beer_garden.local_plugins.manager.lpm_proxy.start()

        self.logger.debug("Starting plugin log config file monitors")
        if config.get("plugin.logging.config_file"):
            self.plugin_log_config_observer.start()
        if config.get("plugin.local.logging.config_file"):
            self.plugin_local_log_config_observer.start()

        if config.get("scheduler.job_startup_file") and os.path.isfile(
            config.get("scheduler.job_startup_file")
        ):
            self.logger.debug("Loading job startup file")
            beer_garden.scheduler.import_jobs(config.get("scheduler.job_startup_file"))

        self.logger.debug("Starting helper threads...")
        for helper_thread in self.helper_threads:
            helper_thread.start()

        self.logger.debug("Publishing to Parent that we are online")
        beer_garden.garden.publish_garden()

        self.logger.info("All set! Let me know if you need anything else!")

    def _shutdown(self, shutdown_failure=False):
        """Shutdown core requirements for Application"""
        self.logger.info(
            "Closing time! You don't have to go home, but you can't stay here."
        )

        try:
            self.logger.debug("Publishing shutdown sync")
            beer_garden.garden.publish_garden(status="STOPPED")
        except Exception as ex:
            self.logger.info("Failed: Publishing shutdown sync")
            self.logger.error(ex)
            shutdown_failure = True

        if self.scheduler.running:
            try:
                self.logger.debug("Pausing scheduler - no more jobs will be run")
                self.scheduler.pause()
            except Exception as ex:
                self.logger.info("Failed: Pausing scheduler - no more jobs will be run")
                self.logger.error(ex)
                shutdown_failure = True

        try:
            self.logger.debug("Stopping plugin log config file monitors")
            self.plugin_log_config_observer.stop()
            self.plugin_local_log_config_observer.stop()
        except Exception as ex:
            self.logger.info("Failed: Stopping plugin log config file monitors")
            self.logger.error(ex)
            shutdown_failure = True

        try:
            self.logger.debug("Stopping forwarding processor...")
            beer_garden.router.forward_processor.stop()
        except Exception as ex:
            self.logger.info("Failed: Stopping forwarding processor")
            self.logger.error(ex)
            shutdown_failure = True

        try:
            self.logger.debug("Stopping helper threads")
            for helper_thread in reversed(self.helper_threads):
                helper_thread.stop()
        except Exception as ex:
            self.logger.info("Failed: Stopping helper threads")
            self.logger.error(ex)
            shutdown_failure = True

        if self.scheduler.running:
            try:
                self.logger.debug("Shutting down scheduler")
                self.scheduler.shutdown(wait=False)
            except Exception as ex:
                self.logger.info("Failed: Shutting down scheduler")
                self.logger.error(ex)
                shutdown_failure = True

        try:
            self.logger.debug("Stopping local plugin process monitoring")
            beer_garden.local_plugins.manager.lpm_proxy.stop()
        except Exception as ex:
            self.logger.info("Failed: Stopping local plugin process monitoring")
            self.logger.error(ex)
            shutdown_failure = True

        try:
            self.logger.debug("Stopping local plugins")
            beer_garden.local_plugins.manager.lpm_proxy.stop_all()
        except Exception as ex:
            self.logger.info("Failed: Stopping local plugins")
            self.logger.error(ex)
            shutdown_failure = True

        try:
            self.logger.debug("Shutting Down local plugin process monitoring")
            self.mp_manager.shutdown()
        except Exception as ex:
            self.logger.info("Failed: Shutting Down local plugin process monitoring")
            self.logger.error(ex)
            shutdown_failure = True

        try:
            self.logger.debug("Stopping entry points")
            self.entry_manager.stop()
        except Exception as ex:
            self.logger.info("Failed: Stopping entry points")
            self.logger.error(ex)
            shutdown_failure = True

        try:
            self.logger.debug("Stopping event manager")
            beer_garden.events.manager.stop()
        except Exception as ex:
            self.logger.info("Failed: Stopping event manager")
            self.logger.error(ex)
            shutdown_failure = True

        if config.get("replication.enabled"):
            try:
                self.logger.debug("Stopping Event Consumer")
                queue.shutdown_event_consumer()
            except Exception as ex:
                self.logger.info("Failed: Stopping Event Consumer")
                self.logger.error(ex)
                shutdown_failure = True

        if shutdown_failure:
            self.logger.info(
                "Unsuccessfully shut down Beer-garden, forcing os.exit. "
                "Please check your processes for orphaned threads"
            )
            os._exit(os.EX_OK)
        else:
            self.logger.info("Successfully shut down Beer-garden")

    def _setup_events_manager(self):
        """Set up the event manager for the Main Processor"""

        if config.get("replication.enabled"):
            event_manager = EventProcessor(name="event manager")
        else:
            event_manager = FanoutProcessor(name="event manager")

        # Forward all events down into the entry points
        event_manager.register(self.entry_manager, manage=False)

        # Register the callback processor
        beer_garden.events.handlers.add_internal_events_handler(event_manager)

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
                    reconnect_action=reconnect_action,
                )
            )

        return event_manager

    @staticmethod
    def _setup_multiprocessing_manager():
        BaseManager.register(
            "PluginManager",
            callable=partial(
                PluginManager,
                plugin_dir=config.get("plugin.local.directory"),
                log_dir=config.get("plugin.local.log_directory"),
                connection_info=config.get("entry.http"),
                username=(
                    config.get("plugin.local.auth.username")
                    if config.get("auth.enabled")
                    else None
                ),
                password=(
                    config.get("plugin.local.auth.password")
                    if config.get("auth.enabled")
                    else None
                ),
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
