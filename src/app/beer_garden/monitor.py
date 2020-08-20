# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
import os

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from beer_garden.events import publish
from brewtils.models import Instance, Request
from brewtils.stoppable_thread import StoppableThread

import beer_garden.db.api as db
import beer_garden.queue.api as queue


class PluginStatusMonitor(StoppableThread):
    """Monitor plugin heartbeats and update plugin status"""

    def __init__(self, heartbeat_interval=10, timeout_seconds=30):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Plugin Status Monitor"
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timedelta(seconds=timeout_seconds)
        self.status_request = Request(command="_status", command_type="EPHEMERAL")

        super(PluginStatusMonitor, self).__init__(
            logger=self.logger, name="PluginStatusMonitor"
        )

    def run(self):
        self.logger.info(self.display_name + " is started")

        while not self.wait(self.heartbeat_interval):
            self.request_status()
            self.check_status()

        self.logger.info(self.display_name + " is stopped")

    def request_status(self):
        try:
            queue.put(
                self.status_request,
                routing_key="admin",
                expiration=str(self.heartbeat_interval * 1000),
            )
        except Exception as ex:
            self.logger.warning("Unable to publish status request: %s", str(ex))

    def check_status(self):
        """Update instance status if necessary"""

        for instance in db.query(Instance):
            if self.stopped():
                break

            last_heartbeat = instance.status_info["heartbeat"]

            if last_heartbeat:
                if (
                    instance.status == "RUNNING"
                    and datetime.utcnow() - last_heartbeat >= self.timeout
                ):
                    instance.status = "UNRESPONSIVE"
                    db.update(instance)
                elif (
                    instance.status
                    in ["UNRESPONSIVE", "STARTING", "INITIALIZING", "UNKNOWN"]
                    and datetime.utcnow() - last_heartbeat < self.timeout
                ):
                    instance.status = "RUNNING"
                    db.update(instance)


class MonitorFile:
    def __init__(self, path, publish_event):
        self.observer = PollingObserver()
        if path:
            self.file = path
            self.path = os.path.split(path)[0]
            self.publish_event = publish_event

            self.event_handler = PatternMatchingEventHandler(
                patterns=[self.file], ignore_patterns=[], ignore_directories=True
            )

            self.event_handler.on_created = self.on_created
            self.event_handler.on_modified = self.on_modified

            # Using PollingObserver instead of Observer because Observer throws events at
            # each file transaction

            self.observer.schedule(self.event_handler, self.path, recursive=False)
        self.observer.start()

    def on_created(self, event):
        """ When a user VIM edits a file it DELETES, then CREATES the file, this captures that use case"""
        publish(self.publish_event)

    def on_modified(self, event):
        """ This captures all other modification events that occur against the file"""
        publish(self.publish_event)

    def stop(self):
        self.observer.stop()
        self.observer.join()
