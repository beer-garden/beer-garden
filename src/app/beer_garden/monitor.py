# -*- coding: utf-8 -*-
"""Monitor Service

These are abstract classes generated to be utilizes for functions based off OS file events
"""
import logging
from pathlib import Path

from brewtils.models import Event, Events, Job
from watchdog.events import PatternMatchingEventHandler, RegexMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from beer_garden.events import publish

logger = logging.getLogger(__name__)


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


class MonitorDirectory(RegexMatchingEventHandler):
    """Monitor files and create Beergarden events

    This is a wrapper around a watchdog PollingObserver. PollingObserver is used instead
    of Observer because Observer throws events on each file transaction.

    Note that the events generated are NOT watchdog events, they are whatever
    Beergarden events are specified during initialization.

    """

    def __init__(
        self,
        path: str,
        pattern: str,
        recursive: bool,
        create: bool,
        modify: bool,
        move: bool,
        delete: bool,
        job: Job = None,
    ):
        super().__init__(regexes=[pattern], ignore_directories=True)

        self._path = path
        self._pattern = pattern
        self._recursive = recursive
        self._create = create
        self._modify = modify
        self._move = move
        self._delete = delete
        self._job = job
        self._observer = PollingObserver()
        self._observer.schedule(self, self._path, recursive=self._recursive)

    def start(self):
        logger.debug(f"Start dir monitor on {self._path}")
        try:
            self._observer.start()
        except RuntimeError:
            self._observer = PollingObserver()
            self._observer.schedule(self, self._path, recursive=self._recursive)
            self._observer.start()

    def stop(self):
        logger.debug(f"Stop dir monitor on {self._path}")
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()

    def on_created(self, event):
        """Callback invoked when the file is created

        When a user VIM edits a file it DELETES, then CREATES the file, this
        captures that case
        """
        if self._create:
            logger.debug(f"Dir file created: {event.src_path} {self._job.id}")
            self.publish_file_event(event)

    def on_modified(self, event):
        """Callback invoked when the file is modified

        This captures all other modification events that occur against the file
        """
        if self._modify:
            logger.debug(f"Dir file modified: {event.src_path} {self._job.id}")
            self.publish_file_event(event)

    def on_moved(self, event):
        """Callback invoked when the file is moved

        This captures if the file is moved into or from the directory
        """
        if self._move:
            logger.debug(f"Dir file moved: {event.src_path} {self._job.id}")
            self.publish_file_event(event)

    def on_deleted(self, event):
        """Callback invoked when the file is deleted

        This captures if the file was deleted (be warned that VIM does this by
        default during write actions)
        """
        if self._delete:
            logger.debug(f"Dir file deleted: {event.src_path} {self._job.id}")
            self.publish_file_event(event)

    def publish_file_event(self, event):
        publish(
            Event(
                name=Events.DIRECTORY_FILE_CHANGE.name,
                metadata={"src_path": event.src_path},
                payload=self._job,
                payload_type=self._job.__class__.__name__,
            )
        )
