# -*- coding: utf-8 -*-
"""Monitor Service

These are abstract classes generated to be utilizes for functions based off OS file events
"""
from pathlib import Path
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from beer_garden.db.mongo.models import Event
from beer_garden.events import publish


class MonitorFile(PatternMatchingEventHandler):
    """Monitor files and create Beergarden events

    This is a wrapper around a watchdog PollingObserver. PollingObserver is used instead
    of Observer because Observer throws events on each file transaction.

    Note that the events generated are NOT watchdog events, they are whatever
    Beergarden events are specified during initialization.

    """

    def __init__(
        self,
        path: str,
        create_event: Event = None,
        modify_event: Event = None,
        moved_event: Event = None,
        deleted_event: Event = None,
    ):
        super().__init__(patterns=[path], ignore_directories=True)

        self._path = path
        self._observer = PollingObserver()

        self.create_event = create_event
        self.modify_event = modify_event
        self.moved_event = moved_event
        self.deleted_event = deleted_event

    def start(self):
        self._observer.schedule(self, Path(self._path).parent, recursive=False)
        self._observer.start()

    def stop(self):
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()

    def on_created(self, _):
        """Callback invoked when the file is created

        When a user VIM edits a file it DELETES, then CREATES the file, this
        captures that case
        """
        if self.create_event:
            publish(self.create_event)

    def on_modified(self, _):
        """Callback invoked when the file is modified

        This captures all other modification events that occur against the file
        """
        if self.modify_event:
            publish(self.modify_event)

    def on_moved(self, _):
        """Callback invoked when the file is moved

        This captures if the file is moved into or from the directory
        """
        if self.moved_event:
            publish(self.moved_event)

    def on_deleted(self, _):
        """Callback invoked when the file is deleted

        This captures if the file was deleted (be warned that VIM does this by
        default during write actions)
        """
        if self.deleted_event:
            publish(self.deleted_event)
