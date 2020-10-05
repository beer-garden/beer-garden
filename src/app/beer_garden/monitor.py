# -*- coding: utf-8 -*-
import os

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from beer_garden.events import publish


class MonitorFile:
    def __init__(
        self,
        path,
        create_event=None,
        modified_event=None,
        moved_event=None,
        deleted_event=None,
    ):

        self.file = path

        if path:
            self.path = os.path.split(path)[0]
            self.create_event = create_event
            self.modified_event = modified_event
            self.moved_event = moved_event
            self.deleted_event = deleted_event

            self.event_handler = PatternMatchingEventHandler(
                patterns=[self.file], ignore_patterns=[], ignore_directories=True
            )

            self.event_handler.on_created = self.on_created
            self.event_handler.on_modified = self.on_modified
            self.event_handler.on_moved = self.on_moved
            self.event_handler.on_deleted = self.on_deleted

            # Using PollingObserver instead of Observer because Observer throws events at
            # each file transaction
            self.observer = PollingObserver()
            self.observer.schedule(self.event_handler, self.path, recursive=False)
            self.observer.start()

    def on_created(self, event):
        """Callback invoked when the file is created

        When a user VIM edits a file it DELETES, then CREATES the file, this
        captures that use case"""
        if self.create_event:
            publish(self.create_event)

    def on_modified(self, event):
        """Callback invoked when the file is moved

        This captures all other modification events that occur against the file"""
        if self.modified_event:
            publish(self.modified_event)

    def on_moved(self, event):
        """Callback invoked when the file is moved

        This captures if the file is moved into or from the directory"""
        if self.moved_event:
            publish(self.moved_event)

    def on_deleted(self, event):
        """Callback invoked when the file is deleted

        This captures if the file was deleted (Be warned that VIM does this by
        default during write actions)"""
        if self.deleted_event:
            publish(self.deleted_event)

    def stop(self):
        if self.file:
            self.observer.stop()
            self.observer.join()
