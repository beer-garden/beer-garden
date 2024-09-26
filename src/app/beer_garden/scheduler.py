# -*- coding: utf-8 -*-
"""Scheduled Service

The schedule service is responsible for:
* CRUD operations of `Job` operations
* Triggering `Job` based `Requests`
"""
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

from apscheduler.events import EVENT_JOB_MAX_INSTANCES
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger as APInterval
from brewtils.errors import ModelValidationError
from brewtils.models import DateTrigger, Event, Events, Job, Operation, Request
from brewtils.schema_parser import SchemaParser
from mongoengine import ValidationError
from pytz import utc

import beer_garden
import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.db.mongo.jobstore import construct_trigger
from beer_garden.events import publish_event
from beer_garden.monitor import MonitorDirectory
from beer_garden.requests import get_request

logger = logging.getLogger(__name__)

observer_threads = dict()


class Monitor(object):
    def __init__(self, job_id, bg_trigger):
        self.job = get_job(job_id)
        self.file_monitor = MonitorDirectory(
            path=bg_trigger.path,
            pattern=bg_trigger.pattern,
            recursive=bg_trigger.recursive,
            create=bg_trigger.create,
            modify=bg_trigger.modify,
            move=bg_trigger.move,
            delete=bg_trigger.delete,
            job=self.job,
        )
        self.start()

    def start(self):
        """Start monitoring a directory"""
        self.file_monitor.start()

    def stop(self):
        """Stop monitoring a directory"""
        self.file_monitor.stop()


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


@pass_through(class_objects=["_sync_scheduler"])
class MixedScheduler(object):
    """
    A wrapper that tracks an interval-based scheduler.
    """

    _sync_scheduler = None

    running = False

    def max_concurrence_listener(scheduler, event):
        db_job = db.query_unique(Job, id=event.job_id)
        db.modify(db_job, inc__skip_count=1)

    def start(self):
        """Starts the scheduler"""
        if self._sync_scheduler is None:
            self._sync_scheduler = BackgroundScheduler()
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
            self._sync_scheduler.configure(**ap_config)
            self._sync_scheduler.add_listener(
                self.max_concurrence_listener, EVENT_JOB_MAX_INSTANCES
            )

            self.internal_scheduled_jobs()

        self._sync_scheduler.start()
        self.running = True
        file_jobs = get_jobs(filter_params={"trigger_type": "file"})
        for job in file_jobs:
            observer_threads[job.id] = Monitor(job.id, job.trigger)

    def resume(self):
        """Resume the scheduler"""
        if self._sync_scheduler:
            self._sync_scheduler.resume()
            self.running = True

    def pause(self):
        """pause the scheduler"""
        if self._sync_scheduler:
            self._sync_scheduler.pause()
            self.running = False

    def shutdown(self, **kwargs):
        """Stops the scheduler

        Args:
            kwargs: Any other scheduler-specific arguments
        """
        self.stop(**kwargs)

    def stop(self, **kwargs):
        """Stops the scheduler

        Args:
            kwargs: Any other scheduler-specific arguments
        """
        if self._sync_scheduler:
            self._sync_scheduler.shutdown(**kwargs)
            self.running = False
            self._sync_scheduler = None

    def reschedule_job(self, job_id, **kwargs):
        """Passes through to the sync scheduler

        Args:
            job_id: The job id
            kwargs: Any other scheduler-specific arguments
        """
        self._sync_scheduler.reschedule_job(job_id, **kwargs)

    def get_job(self, job_id):
        """Looks up a job

        Args:
            job_id: The job id
        """
        return self._sync_scheduler.get_job(job_id)

    def pause_job(self, job_id, **kwargs):
        """Pauses a running job

        Args:
            job_id: The job id
            kwargs: Any other scheduler-specific arguments
        """
        if job_id in observer_threads:
            observer_threads[job_id].stop()
            return
        self._sync_scheduler.pause_job(job_id, **kwargs)

    def resume_job(self, job_id, **kwargs):
        """Resumes a paused job

        Args:
            job_id: The job id
            kwargs: Any other scheduler-specific arguments
        """
        if job_id in observer_threads:
            observer_threads[job_id].start()
            return
        self._sync_scheduler.resume_job(job_id, **kwargs)

    def remove_job(self, job_id, **kwargs):
        """Removes the job from the corresponding scheduler

        Args:
            job_id: The job id to lookup
            kwargs: Any other scheduler-specific arguments
        """
        if job_id in observer_threads:
            remove_job(job_id)
            return
        self._sync_scheduler.remove_job(job_id, **kwargs)

    def execute_job(self, job_id, reset_interval=False, **kwargs):
        """Executes the job ad-hoc

        Args:
            job_id: The job id
            reset_interval: Whether to set the job's interval begin time to now
        """
        job = db.query_unique(Job, id=job_id)
        src_path = kwargs.get("src_path", False)
        if src_path:
            job.request_template.metadata["src_path"] = src_path
        self.add_job(
            run_job,
            trigger=DateTrigger(datetime.utcnow(), timezone="UTC"),
            trigger_type="date",
            coalesce=job.coalesce,
            kwargs={"job_id": job.id, "request_template": job.request_template},
            id="ad-hoc",
        )

        if reset_interval:
            job = beer_garden.application.scheduler.get_job(job_id)
            beer_garden.application.scheduler.reschedule_job(
                job_id, trigger=job.trigger
            )

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

        trigger_type = kwargs.pop("trigger_type")
        bg_trigger = construct_trigger(trigger_type, trigger)
        job_id = kwargs.get("id")
        # Add entry to keep track of file trigger threads
        # Recreate monitor in case the job has been updated
        if job_id and trigger_type == "file":
            if job_id in observer_threads:
                observer_threads[job_id].stop()
                del observer_threads[job_id]
            observer_threads[job_id] = Monitor(job_id, bg_trigger)

        # Add all triggers to schedule except file
        # File triggers will handled by monitor
        if not trigger_type == "file":
            self._sync_scheduler.add_job(
                func,
                trigger=bg_trigger,
                **kwargs,
            )

    def add_schedule(self, func, interval=None, **kwargs):
        """Adds a schedule to one of the schedulers

        Args:
            func: The callback function
            trigger: The trigger used to schedule
            kwargs: Any other kwargs to be passed to the scheduler
        """
        if interval is None:
            logger.exception("Scheduler called with no interval.")
            return

        self._sync_scheduler.add_job(
            func, trigger=APInterval(minutes=interval), **kwargs
        )

    def internal_scheduled_jobs(self):
        # Add scheduled jobs for Mongo Pruner
        prune_interval = config.get("db.prune_interval")
        if prune_interval > 0:
            ttl_config = config.get("db.ttl")
            if ttl_config.get("info") > 0:
                self.add_schedule(
                    beer_garden.db.mongo.pruner.prune_info_requests,
                    interval=prune_interval,
                    max_running_jobs=1,
                )

            if ttl_config.get("action") > 0:
                self.add_schedule(
                    beer_garden.db.mongo.pruner.prune_action_requests,
                    interval=prune_interval,
                    max_running_jobs=1,
                )

            if ttl_config.get("admin") > 0:
                self.add_schedule(
                    beer_garden.db.mongo.pruner.prune_admin_requests,
                    interval=prune_interval,
                    max_running_jobs=1,
                )

            if ttl_config.get("temp") > 0:
                self.add_schedule(
                    beer_garden.db.mongo.pruner.prune_temp_requests,
                    interval=prune_interval,
                    max_running_jobs=1,
                )

            if ttl_config.get("file") > 0:
                self.add_schedule(
                    beer_garden.db.mongo.pruner.prune_files,
                    interval=prune_interval,
                    max_running_jobs=1,
                )

            if ttl_config.get("in_progress") > 0:
                self.add_schedule(
                    beer_garden.db.mongo.pruner.prune_outstanding,
                    interval=prune_interval,
                    max_running_jobs=1,
                )

        # Add scheduled job for checking unresponsive gardens
        self.add_schedule(
            beer_garden.garden.garden_unresponsive_trigger,
            interval=15,
            max_running_jobs=1,
        )

        # Add Garden Sync Scheduler
        if config.get("parent.sync_interval") > 0 and (
            config.get("parent.stomp.enabled") or config.get("parent.http.enabled")
        ):
            self.add_schedule(
                beer_garden.garden.publish_garden,
                interval=config.get("parent.sync_interval"),
                max_running_jobs=1,
            )


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
                model=Request.from_template(request_template),
                model_type="Request",
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
            logger.debug(f"{db_job!r} request completed with {request.status} status")
        elif request.status == "CANCELED":
            updates["inc__canceled_count"] = 1
            logger.debug(f"{db_job!r} request completed with {request.status} status")
        elif request.status == "SUCCESS":
            logger.debug(f"{db_job!r} request completed with SUCCESS status")
            updates["inc__success_count"] = 1

        if updates != {}:
            db.modify(db_job, **updates)
    except Exception as ex:
        logger.error(f"Error executing {db_job}: {ex}")
        db.modify(db_job, inc__error_count=1)

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


def get_jobs(filter_params: Optional[Dict] = None, **kwargs) -> List[Job]:
    return db.query(Job, filter_params=filter_params, **kwargs)


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


def create_jobs(jobs: List[Job]) -> dict:
    """Create multiple new Jobs and add them to the scheduler.

    Args:
        jobs: A list containing the `Job`s to be added

    Returns:
        A dictionary containing the following:
          created: list of brewtils Jobs that were created,
          rejected: list of tuples containing Jobs from the import list that were
                    rejected due to validation errors, along with the error message
                    citing why it was rejected
    """
    created = []
    updated = []
    rejected = []

    for job in jobs:
        try:
            if job.id and db.query(Job, filter_params={"id": job.id}):
                updated.append(update_job(job))
            else:
                created.append(create_job(job))
        except (ModelValidationError, ValidationError) as exc:
            rejected.append((job, str(exc)))

    return {"created": created, "updated": updated, "rejected": rejected}


def import_jobs(jobs_file: str) -> None:
    # Load the jobs file
    with open(jobs_file) as import_file:
        try:
            jobs_json = json.load(import_file)
            jobs = SchemaParser.parse_job(jobs_json, many=True)
            create_jobs(jobs)
        except json.JSONDecodeError:
            logger.debug(f"Failed to import jobs from {jobs_file}")


@publish_event(Events.JOB_UPDATED)
def update_job(job: Job) -> Job:
    """Update a Job and add it to the scheduler

    Args:
        job: The Job to be updated

    Returns:
        The added Job
    """

    # Map over job counts
    original_job = get_job(job.id)

    job.success_count = original_job.success_count
    job.error_count = original_job.error_count
    job.canceled_count = original_job.canceled_count
    job.skip_count = original_job.skip_count

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
    if job_id in observer_threads:
        observer_threads[job_id].stop()
        del observer_threads[job_id]
    # The scheduler takes care of removing the Job from the database
    return db.query_unique(Job, id=job_id)


@publish_event(Events.JOB_EXECUTED)
def execute_job(job_id: str, reset_interval=False) -> Job:
    """Execute a Job ad-hoc

    Creates a new job with a trigger for now.

    Args:
        job_id: The Job ID

    Returns:
        The spawned Request
    """
    job = db.query_unique(Job, id=job_id, raise_missing=True)
    job.reset_interval = reset_interval

    if reset_interval and job.trigger_type != "interval":
        raise ModelValidationError(
            "reset_interval can only be used with trigger type of interval"
        )

    return job


def handle_event(event: Event) -> None:
    """Handle JOB events

    When creating or updating a job, make sure to mark as local first.

    BG should only handle events that are designated for the local environment. If BG
    triggers off a non-local JOB, then the JOB could be ran twice.

    Args:
        event: The event to handle
    """

    if (
        event.garden == config.get("garden.name")
        and beer_garden.application.scheduler.running
    ):
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
        elif event.name == Events.JOB_EXECUTED.name:
            beer_garden.application.scheduler.execute_job(
                event.payload.id,
                jobstore="beer_garden",
                reset_interval=event.payload.reset_interval,
            )
        elif event.name == Events.DIRECTORY_FILE_CHANGE.name:
            beer_garden.application.scheduler.execute_job(
                event.payload.id,
                jobstore="beer_garden",
                reset_interval=None,
                src_path=event.metadata["src_path"],
            )
