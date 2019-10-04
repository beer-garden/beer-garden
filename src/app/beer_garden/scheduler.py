# -*- coding: utf-8 -*-
import logging
from typing import List, Dict

import brewtils.models
from apscheduler.job import Job as APJob
from apscheduler.jobstores.base import BaseJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger as APInterval
from brewtils.schema_parser import SchemaParser
from mongoengine import DoesNotExist
from pytz import utc

import beer_garden
from beer_garden.db.mongo.models import Job as BGJob, Request
from beer_garden.db.mongo.parser import MongoParser
from beer_garden.requests import process_request

logger = logging.getLogger(__name__)


class IntervalTrigger(APInterval):
    """Beergarden implementation of an apscheduler IntervalTrigger"""

    def __init__(self, *args, **kwargs):
        self.reschedule_on_finish = kwargs.pop("reschedule_on_finish", False)
        super(IntervalTrigger, self).__init__(*args, **kwargs)


def construct_trigger(trigger_type, bg_trigger):
    """Construct an apscheduler trigger based on type and mongo document."""
    trigger_type = trigger_type
    trigger_kwargs = bg_trigger.get_scheduler_kwargs()
    if trigger_type == "date":
        return DateTrigger(**trigger_kwargs)
    elif trigger_type == "interval":
        return IntervalTrigger(**trigger_kwargs)
    elif trigger_type == "cron":
        return CronTrigger(**trigger_kwargs)
    else:
        raise ValueError("Invalid trigger type %s" % trigger_type)


def db_to_scheduler(document, scheduler, alias="beer_garden"):
    """Convert a database job to a scheduler's job."""
    job = APJob.__new__(APJob)
    if document.next_run_time:
        next_run_time = utc.localize(document.next_run_time)
    else:
        next_run_time = None
    state = {
        "id": document.id,
        "func": "beer_garden.scheduler:run_job",
        "trigger": construct_trigger(document.trigger_type, document.trigger),
        "executor": "default",
        "args": (),
        "kwargs": {
            "request_template": document.request_template,
            "job_id": str(document.id),
        },
        "name": document.name,
        "misfire_grace_time": document.misfire_grace_time,
        "coalesce": document.coalesce,
        "max_instances": document.max_instances,
        "next_run_time": next_run_time,
    }
    job.__setstate__(state)
    job._scheduler = scheduler
    job._jobstore_alias = alias
    return job


def run_job(job_id, request_template):
    """Spawned by the scheduler, this will kick off a new request.

    This method is meant to be run in a separate process.

    Args:
        job_id: The Beer-Garden job ID that triggered this event.
        request_template: Request template specified by the job.
    """
    request = Request(**request_template.to_mongo())
    request.metadata["_bg_job_id"] = job_id

    # TODO - Possibly allow specifying blocking timeout on the job definition
    # Want to wait for completion here
    process_request(request, wait_timeout=-1)

    try:
        document = BGJob.objects.get(id=job_id)
        if request.status == "ERROR":
            document.error_count += 1
        elif request.status == "SUCCESS":
            document.success_count += 1
        document.save()
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


class BGJobStore(BaseJobStore):
    def lookup_job(self, job_id):
        """Get job from mongo, convert it to an apscheduler Job.

        Args:
            job_id: The ID of the job to get.

        Returns:
            An apscheduler job or None.
        """
        try:
            document = BGJob.objects.get(id=job_id)
            return db_to_scheduler(document, self._scheduler, self._alias)
        except DoesNotExist:
            return None

    def get_due_jobs(self, now):
        """Find due jobs and convert them to apscheduler jobs."""
        return self._get_jobs({"next_run_time__lte": now})

    def get_next_run_time(self):
        """Get the next run time as a localized datetime."""
        try:
            document = (
                BGJob.objects(next_run_time__ne=None)
                .order_by("next_run_time")
                .fields(next_run_time=1)
                .first()
            )

            if document:
                return utc.localize(document.next_run_time)
        except DoesNotExist:
            return None

    def get_all_jobs(self):
        """Get all jobs in apscheduler speak."""
        return self._get_jobs({})

    def add_job(self, job):
        """Just updates the next_run_time.

        Notes:

            The jobstore only needs to update the object that has already
            been saved to the database. It is slightly tricky to generate
            the ``next_run_time`` on the apscheduler job, so we just let
            the scheduler do it for us. After that, we update our job's
            next_run_time to be whatever the scheduler set.

        Args:
            job: The job from the scheduler
        """
        document = BGJob.objects.get(id=job.id)
        document.next_run_time = job.next_run_time
        document.save()

    def update_job(self, job):
        """Update the next_run_time for the job."""
        document = BGJob.objects.get(id=job.id)
        document.next_run_time = job.next_run_time
        document.save()

    def remove_job(self, job_id):
        """Remove job with the given ID."""
        BGJob.objects.get(id=job_id).delete()

    def remove_all_jobs(self):
        """Remove all jobs."""
        BGJob.objects.delete()

    def _get_jobs(self, conditions):
        jobs = []
        failed_jobs = []
        for document in BGJob.objects(**conditions).order_by("next_run_time"):
            try:
                jobs.append(db_to_scheduler(document, self._scheduler, self._alias))
            except Exception:
                logger.exception(
                    "Removing job %s, exception occurred while restoring:" % document.id
                )
                failed_jobs.append(document)

        # Remove all the jobs we failed to restore
        if failed_jobs:
            for document in failed_jobs:
                document.delete()

        return jobs


def get_job(job_id: str) -> brewtils.models.Job:
    return SchemaParser.parse_job(
        SchemaParser.serialize_job(BGJob.objects.get(id=job_id), to_string=False),
        from_string=False,
    )


def get_jobs(filter_params: Dict = None) -> List[brewtils.models.Job]:
    return SchemaParser.parse_job(
        SchemaParser.serialize_job(
            BGJob.objects.filter(**filter_params or {}), to_string=False, many=True
        ),
        from_string=False,
        many=True,
    )


def create_job(job: brewtils.models.Job) -> brewtils.models.Job:
    """Create a new Job and add it to the scheduler

    Args:
        job: The Job to be added

    Returns:
        The added Job
    """
    job = MongoParser.parse_job(
        SchemaParser.serialize_job(job, to_string=False), from_string=False
    )

    # We have to save here, because we need an ID to pass
    # to the scheduler.
    job.save()

    try:
        beer_garden.application.scheduler.add_job(
            run_job,
            None,
            kwargs={"request_template": job.request_template, "job_id": str(job.id)},
            name=job.name,
            misfire_grace_time=job.misfire_grace_time,
            coalesce=job.coalesce,
            max_instances=job.max_instances,
            jobstore="beer_garden",
            replace_existing=False,
            id=str(job.id),
        )
    except Exception:
        job.delete()
        raise

    return SchemaParser.parse_job(
        SchemaParser.serialize_job(job, to_string=False), from_string=False
    )


def pause_job(job_id: str) -> brewtils.models.Job:
    """Pause a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """
    beer_garden.application.scheduler.pause_job(job_id, jobstore="beer_garden")

    job = BGJob.objects.get(id=job_id)
    job.status = "PAUSED"
    job.save()

    return SchemaParser.parse_job(
        SchemaParser.serialize_job(job, to_string=False), from_string=False
    )


def resume_job(job_id: str) -> brewtils.models.Job:
    """Resume a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """
    beer_garden.application.scheduler.resume_job(job_id, jobstore="beer_garden")

    job = BGJob.objects.get(id=job_id)
    job.status = "RUNNING"
    job.save()

    return SchemaParser.parse_job(
        SchemaParser.serialize_job(job, to_string=False), from_string=False
    )


def remove_job(job_id: str) -> None:
    """Remove a Job

    Args:
        job_id: The Job ID

    Returns:
        None
    """
    # TODO - Should this be removing the Job from the DB?

    beer_garden.application.scheduler.remove_job(job_id, jobstore="beer_garden")
