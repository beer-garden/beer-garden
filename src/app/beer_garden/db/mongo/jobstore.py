# -*- coding: utf-8 -*-
import logging

from apscheduler.job import Job as APJob
from apscheduler.jobstores.base import BaseJobStore
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger as APInterval
from brewtils.models import Job
from pytz import utc

from beer_garden.db.mongo.api import delete, query, query_unique, update
from beer_garden.db.mongo.models import Job as MongoJob

logger = logging.getLogger(__name__)


class IntervalTrigger(APInterval):
    """Beergarden implementation of an apscheduler IntervalTrigger"""

    def __init__(self, *args, **kwargs):
        self.reschedule_on_finish = kwargs.pop("reschedule_on_finish", False)
        super(IntervalTrigger, self).__init__(*args, **kwargs)


def construct_trigger(trigger_type: str, bg_trigger) -> BaseTrigger:
    """Convert a Beergarden trigger to an APScheduler one."""
    if trigger_type == "date":
        return DateTrigger(**bg_trigger.scheduler_kwargs)
    elif trigger_type == "interval":
        return IntervalTrigger(**bg_trigger.scheduler_kwargs)
    elif trigger_type == "cron":
        return CronTrigger(**bg_trigger.scheduler_kwargs)
    else:
        raise ValueError("Trigger type %s not supported by APScheduler" % trigger_type)


def construct_job(job: Job, scheduler, alias="beer_garden"):
    """Convert a Beergarden job to an APScheduler one."""
    if job is None:
        return None

    trigger = construct_trigger(job.trigger_type, job.trigger)
    next_run_time = utc.localize(job.next_run_time) if job.next_run_time else None

    ap_job = APJob.__new__(APJob)
    ap_job._scheduler = scheduler
    ap_job._jobstore_alias = alias
    ap_job.__setstate__(
        {
            "id": job.id,
            "func": "beer_garden.scheduler:run_job",
            "trigger": trigger,
            "executor": "default",
            "args": (),
            "kwargs": {"request_template": job.request_template, "job_id": job.id},
            "name": job.name,
            "misfire_grace_time": job.misfire_grace_time,
            "coalesce": job.coalesce,
            "max_instances": job.max_instances,
            "next_run_time": next_run_time,
        }
    )

    return ap_job


class MongoJobStore(BaseJobStore):
    def lookup_job(self, job_id):
        """Get job from mongo, convert it to an apscheduler Job.

        Args:
            job_id: The ID of the job to get.

        Returns:
            An apscheduler job or None.
        """
        return construct_job(query_unique(Job, id=job_id), self._scheduler, self._alias)

    def get_due_jobs(self, now):
        """Find due jobs and convert them to apscheduler jobs."""
        return self._get_jobs({"next_run_time__lte": now})

    def get_next_run_time(self):
        """Get the next run time as a localized datetime."""
        jobs = query(
            Job,
            filter_params={"next_run_time__ne": None},
            include_fields=["next_run_time"],
            order_by="next_run_time",
        )

        return None if not jobs else utc.localize(jobs[0].next_run_time)

    def get_all_jobs(self):
        """Get all jobs in apscheduler speak."""
        return self._get_jobs()

    def add_job(self, job: APJob) -> None:
        """Just updates the next_run_time.

        Notes:
            The jobstore only needs to update the object that has already been saved to
            the database. It is slightly tricky to generate the ``next_run_time`` on the
             apscheduler job, so we just let the scheduler do it for us. After that, we
             update our job's next_run_time to be whatever the scheduler set.

        Args:
            job: The job from the scheduler
        """
        db_job = query_unique(Job, id=job.kwargs["job_id"])
        db_job.next_run_time = job.next_run_time
        update(db_job)

    def update_job(self, job: APJob) -> None:
        """Update the next_run_time for the job."""
        db_job = query_unique(Job, id=job.id)
        db_job.next_run_time = job.next_run_time
        update(db_job)

    def remove_job(self, job_id):
        """Remove job with the given ID."""
        delete(query_unique(Job, id=job_id))

    def remove_all_jobs(self):
        """Remove all jobs."""
        MongoJob.objects.delete()

    def _get_jobs(self, conditions=None):
        jobs = []
        failed_jobs = []

        for job in query(Job, filter_params=conditions, order_by="next_run_time"):
            try:
                jobs.append(construct_job(job, self._scheduler, self._alias))
            except Exception as ex:
                failed_jobs.append(job)
                logger.exception(
                    f"Exception while restoring job {job.id}, about to remove: {ex}"
                )

        # Remove all the jobs we failed to restore
        for job in failed_jobs:
            delete(job)

        return jobs
