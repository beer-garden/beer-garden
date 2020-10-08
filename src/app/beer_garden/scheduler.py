# -*- coding: utf-8 -*-
import logging
import threading
from typing import Dict, List

from apscheduler.triggers.interval import IntervalTrigger as APInterval

from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import (PatternMatchingEventHandler, EVENT_TYPE_CREATED, EVENT_TYPE_DELETED,
                             EVENT_TYPE_MOVED, EVENT_TYPE_MODIFIED)
from watchdog.utils import (has_attribute, unicode_paths)
from pathtools.patterns import match_any_paths

from apscheduler.schedulers.background import BackgroundScheduler

from brewtils.models import Event, Events, Job

import beer_garden
import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.events import publish_event
from beer_garden.requests import process_request
from brewtils.models import FileTrigger

logger = logging.getLogger(__name__)





class PatternMatchingEventHandlerWithArgs(PatternMatchingEventHandler):
    _args = []
    _kwargs = {}

    def __init__(self, args=[], kwargs={},  **thru):
        self._args = args
        self._kwargs = kwargs
        # print("Event Handler found: ARGS- %s  KWARGS- %s" %(args, kwargs))
        super().__init__(**thru)

    # Copy the dispatch code, but include arguments if specified
    def dispatch(self, event):
        """Dispatches events to the appropriate methods.

                :param event:
                    The event object representing the file system event.
                :type event:
                    :class:`FileSystemEvent`
                """
        if self.ignore_directories and event.is_directory:
            return

        paths = []
        if has_attribute(event, 'dest_path'):
            paths.append(unicode_paths.decode(event.dest_path))
        if event.src_path:
            paths.append(unicode_paths.decode(event.src_path))

        if match_any_paths(paths,
                           included_patterns=self.patterns,
                           excluded_patterns=self.ignore_patterns,
                           case_sensitive=self.case_sensitive):
            self.on_any_event(*self._args, file_trigger_event=event, **self._kwargs)
            _method_map = {
                EVENT_TYPE_MODIFIED: self.on_modified,
                EVENT_TYPE_MOVED: self.on_moved,
                EVENT_TYPE_CREATED: self.on_created,
                EVENT_TYPE_DELETED: self.on_deleted,
            }
            event_type = event.event_type
            # print("Event Handler Calling %s, %s" % (self._args, self._kwargs))
            _method_map[event_type](*self._args, file_trigger_event=event, **self._kwargs)

    def on_created(self, *args, file_trigger_event=None, **kwargs):
        super().on_created(file_trigger_event)

    def on_any_event(self, *args, file_trigger_event=None, **kwargs):
        super().on_any_event(file_trigger_event)

    def on_deleted(self, *args, file_trigger_event=None, **kwargs):
        super().on_deleted(file_trigger_event)

    def on_modified(self, *args, file_trigger_event=None, **kwargs):
        super().on_modified(file_trigger_event)

    def on_moved(self, *args, file_trigger_event=None, **kwargs):
        super().on_moved(file_trigger_event)


def passthrough(class_objs=[]):
    """
    Adds any non-implemented methods defined by the given object names to the class.
    :param class_objs: List of class object names to expose directly.
    :return:
    """
    def wrapper(my_class):
        for obj in class_objs:
            scheduler = getattr(my_class, obj, None)
            if scheduler is not None:
                method_list = [func for func in dir(scheduler) if callable(getattr(scheduler, func))]
                # added = []
                for name in method_list:
                    # Don't expose methods that are intended to be private!
                    if name[0] != '_' and not hasattr(my_class, name):
                        # added.append(name)
                        method = getattr(scheduler, name)
                        setattr(my_class, name, method)
                # print("%s object has methods : %s" % (obj, added))
        return my_class
    return wrapper

def sanity_check(*args, **kwargs):
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ENTERED SANITY!!")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SANITY ARGS: %s, KWARGS: %s" % (args, kwargs))


@passthrough(class_objs=['_sync_scheduler', '_async_scheduler'])
class MixedScheduler(object):
    """
    A wrapper that tracks a file-based scheduler and an interval-based scheduler.
    """
    _sync_scheduler = BackgroundScheduler()
    _async_scheduler = Observer()
    _async_jobs = set()

    running = False

    def __init__(self, interval_config=None, file_config=None):
        # print(interval_config)
        self._sync_scheduler.configure(**interval_config)
        # self._sync_scheduler = BackgroundScheduler(**interval_config)

    def start(self):
        self._sync_scheduler.start()
        self._async_scheduler.start()
        self.running = True

    def shutdown(self, **kwargs):
        self.stop(**kwargs)

    def stop(self, **kwargs):
        self._sync_scheduler.shutdown(**kwargs)
        self._async_scheduler.stop()
        self.running = False

    def get_job(self, job_id):
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SCHEDULER GET JOB event captured!")
        if job_id not in self._async_jobs:
            # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~NOT IN ASYNC_JOBS')
            return self._sync_scheduler.get_job(job_id)
        else:
            return db.query_unique(Job, id=job_id)


    def add_job(self, func, trigger=None, **kwargs):
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~SCHEDULER_ADD_JOB event captured!")
        if trigger is None:
            return

        if not isinstance(trigger, FileTrigger):
            kwargs.pop('request_template')
            # print('Recieved job request (SYNC): %s, %s, %s' % (func.__name__, trigger, kwargs))
            self._sync_scheduler.add_job(func, trigger=None, **kwargs)
        else:
            # print('Recieved job request (ASYNC): %s, %s' % (func.__name__, trigger))
            args = [kwargs.get('id'), kwargs.get('request_template')]
            event_handler = PatternMatchingEventHandlerWithArgs(args=args, patterns=["*"+trigger.pattern])
            event_handler.on_any_event = func
            if trigger.path is not None and event_handler is not None:
                self._async_jobs.add(kwargs.get('id'))
                self._async_scheduler.schedule(event_handler, trigger.path, recursive=trigger.recursive)
                # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Scheduled a file watch! %s' % (trigger.path+"/"+trigger.pattern))
                # import time
                # time.sleep(1)
                # with open(trigger.path+"/"+trigger.pattern, 'w') as fp:
                #     fp.write("Crocodile")
                # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Wrote!")


class IntervalTrigger(APInterval):
    """Beergarden implementation of an apscheduler IntervalTrigger"""

    def __init__(self, *args, **kwargs):
        self.reschedule_on_finish = kwargs.pop("reschedule_on_finish", False)
        super(IntervalTrigger, self).__init__(*args, **kwargs)


def run_job(job_id, request_template, **kwargs):
    """Spawned by the scheduler, this will kick off a new request.

    This method is meant to be run in a separate process.

    Args:
        job_id: The Beer-Garden job ID that triggered this event.
        request_template: Request template specified by the job.
    """
    request_template.metadata["_bg_job_id"] = job_id

    # TODO - Possibly allow specifying blocking timeout on the job definition
    wait_event = threading.Event()
    # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Sending request to be processed")
    request = process_request(request_template, wait_event=wait_event)
    wait_event.wait()

    # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Request completed")

    try:
        db_job = db.query_unique(Job, id=job_id)
        if db_job:
            if request.status == "ERROR":
                db_job.error_count += 1
            elif request.status == "SUCCESS":
                db_job.success_count += 1
            db.update(db_job)
        else:
            # If the job is not in the database, don't proceed to update scheduler
            return
    except Exception as ex:
        logger.exception(f"Could not update job counts: {ex}")

    # Be a little careful here as the job could have been removed or paused
    job = beer_garden.application.scheduler.get_job(job_id)
    if (
        job
        and job.next_run_time is not None
        and getattr(job.trigger, "reschedule_on_finish", False)
    ):
        # This essentially resets the timer on this job, which has the effect of
        # making the wait time start whenever the job finishes
        beer_garden.application.scheduler.reschedule_job(job_id, trigger=job.trigger)


def get_job(job_id: str) -> Job:
    return db.query_unique(Job, id=job_id)


def get_jobs(filter_params: Dict = None) -> List[Job]:
    return db.query(Job, filter_params=filter_params)


@publish_event(Events.JOB_CREATED)
def create_job(job: Job) -> Job:
    """Create a new Job and add it to the scheduler

    Args:
        job: The Job to be added

    Returns:
        The added Job
    """
    # Save first so we have an ID to pass to the scheduler
    job = db.create(job)

    return job


@publish_event(Events.JOB_PAUSED)
def pause_job(job_id: str) -> Job:
    """Pause a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """

    job = db.query_unique(Job, id=job_id)
    job.status = "PAUSED"
    job = db.update(job)

    return job


@publish_event(Events.JOB_RESUMED)
def resume_job(job_id: str) -> Job:
    """Resume a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """

    job = db.query_unique(Job, id=job_id)
    job.status = "RUNNING"
    job = db.update(job)

    return job


@publish_event(Events.JOB_DELETED)
def remove_job(job_id: str) -> None:
    """Remove a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job ID
    """
    # The scheduler takes care of removing the Job from the database
    return db.query_unique(Job, id=job_id)


def handle_event(event: Event) -> None:
    """Handle JOB events

    When creating or updating a job, make sure to mark as local first.

    BG should only handle events that are designated for the local environment. If BG
    triggers off a non-local JOB, then the JOB could be ran twice.

    Args:
        event: The event to handle
    """

    if event.garden == config.get("garden.name"):

        if event.name == Events.JOB_CREATED.name:
            try:
                # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~JOB_CREATED event captured!")
                # print("Payload: %s" % event.payload.trigger)
                beer_garden.application.scheduler.add_job(
                    run_job,
                    trigger=event.payload.trigger,
                    kwargs={
                        "request_template": event.payload.request_template,
                        "job_id": str(event.payload.id),
                    },
                    name=event.payload.name,
                    misfire_grace_time=event.payload.misfire_grace_time,
                    coalesce=event.payload.coalesce,
                    max_instances=event.payload.max_instances,
                    jobstore="beer_garden",
                    replace_existing=False,
                    id=str(event.payload.id),
                    request_template=event.payload.request_template,
                )
            except Exception:
                db.delete(event.payload)
                raise

        elif event.name == Events.JOB_PAUSED.name:
            beer_garden.application.scheduler.pause_job(
                event.payload.id, jobstore="beer_garden"
            )
        elif event.name == Events.JOB_RESUMED.name:
            beer_garden.application.scheduler.resume_job(
                event.payload.id, jobstore="beer_garden"
            )
        elif event.name == Events.JOB_DELETED.name:
            beer_garden.application.scheduler.remove_job(
                event.payload.id, jobstore="beer_garden"
            )
