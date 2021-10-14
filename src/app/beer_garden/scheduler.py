# -*- coding: utf-8 -*-
"""Scheduled Service

The schedule service is responsible for:
* CRUD operations of `Job` operations
* Triggering `Job` based `Requests`
"""
import json
import logging
import threading
from datetime import datetime, timedelta
from operator import attrgetter, methodcaller
from os.path import isdir
from typing import Dict, List, Optional

import mongoengine
import pymongo
import pymongo.database
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger as APInterval
from brewtils.models import Event, Events, FileTrigger, Job, Operation
from brewtils.schema_parser import SchemaParser
from bson import ObjectId, json_util
from pathtools.patterns import match_any_paths
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.results import InsertManyResult
from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED,
    PatternMatchingEventHandler,
)
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.utils import has_attribute, unicode_paths

import beer_garden
import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.db.mongo.api import from_brewtils
from beer_garden.db.mongo.jobstore import construct_trigger
from beer_garden.events import publish_event
from beer_garden.requests import get_request

logger = logging.getLogger(__name__)


class InjectionDict(dict):
    """
    Dictionary object with overloaded __missing__ function to
    facilitate partial string.format operations
    """

    def __missing__(self, key):
        return "{" + key + "}"


def build_injection_dict(dictionary, obj, prefix="", separator="/"):
    """Populate a dictionary with class variables of an object

    Args:
        dictionary: A dict-like object to fill
        obj: An object with some number of variables (e.g MyObj.my_var)
        prefix: A string to prepend the variable names with
        separator: A string to separate the prefix and variable names

    """
    for item in dir(obj):
        if not callable(getattr(obj, item)):
            if prefix != "":
                dictionary[prefix + separator + item] = getattr(obj, item)
            else:
                dictionary[item] = getattr(obj, item)


def inject_values(request, dictionary):
    """Inject values into a request

    inject_values looks for string fields and attempts
    to format() them with the dictionary provided.

    Args:
        request: An object that may hold string fields with valid str.format() syntax
        dictionary: A dict-like object to pass through to the format() call
    """
    if isinstance(request, dict):
        for k, v in request.items():
            try:
                request[k] = inject_values(v, dictionary)
            except (ReferenceError, IndexError):
                pass
        return request

    elif isinstance(request, str):
        try:
            return request.format_map(dictionary)
        except (AttributeError, KeyError, ValueError):
            return request

    elif isinstance(request, list):
        for i, item in enumerate(request):
            try:
                request[i] = inject_values(item, dictionary)
            except IndexError:
                pass
        return request

    else:
        return request


class PatternMatchingEventHandlerWithArgs(PatternMatchingEventHandler):
    """
    A BG implementation of the watchdog PatternMatchingEventHandler.

    Allows args/kwargs to be stored and passed through to the callback functions
    """

    _args = []
    _kwargs = {}
    _coalesce = False
    _src_path_timing = {}
    # This is used to avoid multiple triggers from the same event
    _min_delta_time = timedelta(microseconds=500_000)

    def __init__(self, args=None, kwargs=None, coalesce=False, **thru):
        self._args = args if args is not None else []
        self._kwargs = kwargs if kwargs is not None else {}
        self._coalesce = coalesce
        super().__init__(**thru)

    # Copy the dispatch code, but include arguments if specified
    def dispatch(self, event):
        """Dispatches events to the appropriate methods."""
        current_time = datetime.now()
        if self.ignore_directories and event.is_directory:
            return

        paths = []
        if has_attribute(event, "dest_path"):
            paths.append(unicode_paths.decode(event.dest_path))
        if event.src_path:
            paths.append(unicode_paths.decode(event.src_path))

        if match_any_paths(
            paths,
            included_patterns=self.patterns,
            excluded_patterns=self.ignore_patterns,
            case_sensitive=self.case_sensitive,
        ):
            _method_map = {
                EVENT_TYPE_MODIFIED: self.on_modified,
                EVENT_TYPE_MOVED: self.on_moved,
                EVENT_TYPE_CREATED: self.on_created,
                EVENT_TYPE_DELETED: self.on_deleted,
            }
            event_type = event.event_type
            event_tuple = (event.src_path, event_type)

            if not self._coalesce:
                self.on_any_event(*self._args, event=event, **self._kwargs)
                _method_map[event_type](*self._args, event=event, **self._kwargs)

            elif event_tuple in self._src_path_timing:
                if (
                    current_time - self._src_path_timing[event_tuple]
                    > self._min_delta_time
                ):
                    # Update the time
                    self._src_path_timing[event_tuple] = datetime.now()

                    self.on_any_event(*self._args, event=event, **self._kwargs)
                    _method_map[event_type](*self._args, event=event, **self._kwargs)
            else:
                self._src_path_timing[event_tuple] = datetime.now()

                self.on_any_event(*self._args, event=event, **self._kwargs)
                _method_map[event_type](*self._args, event=event, **self._kwargs)

    def on_created(self, *args, event=None, **kwargs):
        super().on_created(event)

    def on_any_event(self, *args, event=None, **kwargs):
        super().on_any_event(event)

    def on_deleted(self, *args, event=None, **kwargs):
        super().on_deleted(event)

    def on_modified(self, *args, event=None, **kwargs):
        super().on_modified(event)

    def on_moved(self, *args, event=None, **kwargs):
        super().on_moved(event)


def pass_through(class_objects=None):
    """
    Adds any non-implemented methods defined by the given object names to the class.

    Args:
        class_objects: List of class object names to expose directly.
    """

    def wrapper(my_class):
        for obj in class_objects:
            scheduler = getattr(my_class, obj, None)
            if scheduler is not None:
                method_list = [
                    func
                    for func in dir(scheduler)
                    if callable(getattr(scheduler, func))
                ]
                # added = []
                for name in method_list:
                    # Don't expose methods that are intended to be private!
                    if name[0] != "_" and not hasattr(my_class, name):
                        # added.append(name)
                        method = getattr(scheduler, name)
                        setattr(my_class, name, method)
        return my_class

    return wrapper


@pass_through(class_objects=["_sync_scheduler", "_async_scheduler"])
class MixedScheduler(object):
    """
    A wrapper that tracks a file-based scheduler and an interval-based scheduler.
    """

    _sync_scheduler = BackgroundScheduler()
    _async_scheduler = Observer()
    _async_jobs = {}
    _async_paused_jobs = set()

    running = False

    def _process_watches(self, jobs):
        """Helper function for initialize_from_db.  Adds job list to the scheduler

        Args:
            jobs: Jobs to be added to the watchdog scheduler
        """
        for job in jobs:
            if isinstance(job.trigger, FileTrigger):
                self.add_job(
                    run_job,
                    trigger=job.trigger,
                    coalesce=job.coalesce,
                    kwargs={"job_id": job.id, "request_template": job.request_template},
                )

    def __init__(self, interval_config=None):
        """Initializes the underlying scheduler(s)

        Args:
            interval_config: Any scheduler-specific arguments for the APScheduler
        """
        self._sync_scheduler.configure(**interval_config)

    def initialize_from_db(self):
        """Initializes the watchdog scheduler from jobs stored in the database"""
        all_jobs = db.query(Job, filter_params={"trigger_type": "file"})
        self._process_watches(all_jobs)

    def start(self):
        """Starts both schedulers"""
        self._sync_scheduler.start()
        self._async_scheduler.start()
        self.running = True

    def shutdown(self, **kwargs):
        """Stops both schedulers

        Args:
            kwargs: Any other scheduler-specific arguments
        """
        self.stop(**kwargs)

    def stop(self, **kwargs):
        """Stops both schedulers

        Args:
            kwargs: Any other scheduler-specific arguments
        """
        self._sync_scheduler.shutdown(**kwargs)
        self._async_scheduler.stop()
        self.running = False

    def reschedule_job(self, job_id, **kwargs):
        """Passes through to the sync scheduler, but ignores async jobs

        Args:
            job_id: The job id
            kwargs: Any other scheduler-specific arguments
        """
        if job_id not in self._async_jobs:
            self._sync_scheduler.reschedule_job(job_id, **kwargs)

    def get_job(self, job_id):
        """Looks up a job

        Args:
            job_id: The job id
        """
        if job_id in self._async_jobs:
            return db.query_unique(Job, id=job_id)
        else:
            return self._sync_scheduler.get_job(job_id)

    def pause_job(self, job_id, **kwargs):
        """Pauses a running job

        Args:
            job_id: The job id
            kwargs: Any other scheduler-specific arguments
        """
        if job_id in self._async_jobs:
            if job_id not in self._async_paused_jobs:
                (event_handler, watch) = self._async_jobs.get(job_id)
                self._async_scheduler.remove_handler_for_watch(event_handler, watch)
                self._async_paused_jobs.add(job_id)
        else:
            self._sync_scheduler.pause_job(job_id, **kwargs)

    def resume_job(self, job_id, **kwargs):
        """Resumes a paused job

        Args:
            job_id: The job id
            kwargs: Any other scheduler-specific arguments
        """
        if job_id in self._async_jobs:
            if job_id in self._async_paused_jobs:
                (event_handler, watch) = self._async_jobs.get(job_id)
                self._async_scheduler.add_handler_for_watch(event_handler, watch)
                self._async_paused_jobs.remove(job_id)
        else:
            self._sync_scheduler.resume_job(job_id, **kwargs)

    def remove_job(self, job_id, **kwargs):
        """Removes the job from the corresponding scheduler

        Args:
            job_id: The job id to lookup
            kwargs: Any other scheduler-specific arguments
        """
        if job_id in self._async_jobs:
            self._async_jobs.pop(job_id)
            # Clean up the
            if job_id in self._async_paused_jobs:
                self._async_paused_jobs.remove(job_id)

            db.delete(db.query_unique(Job, id=job_id))
        else:
            self._sync_scheduler.remove_job(job_id, **kwargs)

    def _add_triggers(self, handler, triggers, func):
        """Attaches the function to the handler callback

        Args:
            handler: The event handler
            triggers: A dictionary of triggers that maps callback method
                names to boolean values (e.g. on_moved -> True)
            func: The callback function

        Returns:
            The altered handler
        """
        for name in triggers.keys():
            if hasattr(handler, name) and triggers.get(name):
                setattr(handler, name, func)
        return handler

    def add_job(self, func, trigger=None, **kwargs):
        """Adds a job to one of the schedulers

        Args:
            func: The callback function
            trigger: The trigger used to schedule
            kwargs: Any other kwargs to be passed to the scheduler
        """
        if trigger is None:
            logger.exception("Scheduler called with None-type trigger.")
            return

        if not isinstance(trigger, FileTrigger):
            # The old code always set the trigger to None, not sure why
            self._sync_scheduler.add_job(
                func,
                trigger=construct_trigger(kwargs.pop("trigger_type"), trigger),
                **kwargs,
            )

        else:
            if not isdir(trigger.path):
                logger.exception(f"User passed an invalid trigger path {trigger.path}")
                return

            # Pull out the arguments needed by the run_job function
            args = [
                kwargs.get("kwargs").get("job_id"),
                kwargs.get("kwargs").get("request_template"),
            ]

            # Pass in those args to be relayed once the event occurs
            event_handler = PatternMatchingEventHandlerWithArgs(
                args=args,
                coalesce=kwargs.get("coalesce", False),
                patterns=trigger.pattern,
            )
            event_handler = self._add_triggers(event_handler, trigger.callbacks, func)

            if trigger.path is not None and event_handler is not None:
                # Register the job id with the set and schedule it with watchdog
                watch = self._async_scheduler.schedule(
                    event_handler, trigger.path, recursive=trigger.recursive
                )
                self._async_jobs[args[0]] = (event_handler, watch)


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
    import beer_garden.router

    request_template.metadata["_bg_job_id"] = job_id

    # Attempt to inject information into the request template
    if "event" in kwargs and kwargs["event"] is not None:
        try:
            # This overloads the __missing__ function to allow partial injections
            injection_dict = InjectionDict()
            build_injection_dict(injection_dict, kwargs["event"], prefix="event")

            try:
                db_job = db.query_unique(Job, id=job_id)
                if db_job:
                    build_injection_dict(
                        injection_dict, db_job.trigger, prefix="trigger"
                    )

            except Exception as ex:
                logger.exception(f"Could not fetch job for parameter injection: {ex}")

            inject_values(request_template.parameters, injection_dict)
        except Exception as ex:
            logger.exception(f"Could not inject parameters: {ex}")

    db_job = db.query_unique(Job, id=job_id)
    wait_event = threading.Event()

    # I'm not sure what would cause this, but just be safe
    if not db_job:
        logger.error(f"Could not find job {job_id} in database, job will not be run")
        return

    try:
        logger.debug(f"About to execute {db_job!r}")

        request = beer_garden.router.route(
            Operation(
                operation_type="REQUEST_CREATE",
                model=request_template,
                model_type="RequestTemplate",
                kwargs={"wait_event": wait_event},
            )
        )

        # Wait for the request to complete
        timeout = db_job.timeout or None
        if not wait_event.wait(timeout=timeout):
            logger.warning(f"Execution of job {db_job} timed out.")
            return

        request = get_request(request.id)

        updates = {}
        if request.status == "ERROR":
            updates["inc__error_count"] = 1
            logger.debug(f"{db_job!r} request completed with ERROR status")
        elif request.status == "SUCCESS":
            logger.debug(f"{db_job!r} request completed with SUCCESS status")
            updates["inc__success_count"] = 1

        db.modify(db_job, **updates)
    except Exception as ex:
        logger.exception(f"Error executing {db_job}: {ex}")

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


def get_jobs(filter_params: Optional[Dict] = None) -> List[Job]:
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


def create_jobs(jobs: List[Job]) -> List[str]:
    """Create multiple new Jobs and add them to the scheduler.

    Args:
        jobs: A list containing the `Job`s to be added

    Returns:
        A list containing the `id`s of the `Job`s that were added
    """
    job_collection_name = "job"
    id_key, oid_key = "_id", "$oid"

    # we want the addition of Jobs to obey ACID: either all will succeed or none
    # will succeed; hence we skip using mongoengine and use the pymongo library
    # directly
    the_connection: pymongo.MongoClient = mongoengine.get_connection()
    the_db: pymongo.database.Database = mongoengine.get_db()

    session: ClientSession
    with the_connection.start_session() as session:
        job_collection: Collection = the_db.get_collection(job_collection_name)

        to_mongo_caller = methodcaller("to_mongo")
        job_bson_objects = map(to_mongo_caller, map(from_brewtils, jobs))

        # the below commented code does not work for mongodb running standalone;
        # proper transactions are only supported when the database instance is a
        # replica set or a distributed cluster
        # (maybe one more point for getting rid of mongodb...)
        #
        # this is left here for reference in case anything changes; for example,
        # a user actually running mongo in a replica set, in which case code to
        # determine if that's the case can be added and then the following will
        # work as intended:
        #
        # with session.start_transaction():
        #     result: InsertManyResult = job_collection.insert_many(
        #         job_bson_objects, session=session
        #     )
        #     job_ids_created_list = result.inserted_ids

        result: InsertManyResult = job_collection.insert_many(
            job_bson_objects, session=session
        )
        job_ids_created_list: List[ObjectId] = result.inserted_ids
        jobs_created_cursor: Cursor = job_collection.find(
            {id_key: {"$in": job_ids_created_list}}
        )

    # if we've reached this point, job_ids_created_list and jobs_created_cursor exist

    @publish_event(Events.JOB_CREATED)
    def publish_the_job_created(raw_job):
        """Parse the job to a brewtils Job after replacing the unusable `id`."""
        raw_object_id: ObjectId = raw_job.pop(id_key)
        object_id_as_dict = json.loads(json_util.dumps(raw_object_id))
        raw_job["id"] = object_id_as_dict[oid_key]

        # the `publish_event` wrapper needs the whole Job object
        return SchemaParser.parse_job(raw_job)

    # but we're only interested in the `id` field
    return list(
        map(attrgetter("id"), map(publish_the_job_created, jobs_created_cursor))
    )


@publish_event(Events.JOB_UPDATED)
def update_job(job: Job) -> Job:
    """Update a Job and add it to the scheduler

    Args:
        job: The Job to be updated

    Returns:
        The added Job
    """

    return db.update(job)


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

        if event.name in [Events.JOB_CREATED.name, Events.JOB_UPDATED.name]:
            try:
                beer_garden.application.scheduler.add_job(
                    run_job,
                    trigger=event.payload.trigger,
                    trigger_type=event.payload.trigger_type,
                    kwargs={
                        "request_template": event.payload.request_template,
                        "job_id": str(event.payload.id),
                    },
                    name=event.payload.name,
                    misfire_grace_time=event.payload.misfire_grace_time,
                    coalesce=event.payload.coalesce,
                    max_instances=event.payload.max_instances,
                    jobstore="beer_garden",
                    replace_existing=True,
                    id=event.payload.id,
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
