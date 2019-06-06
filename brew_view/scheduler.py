# -*- coding: utf-8 -*-
from apscheduler.job import Job as APJob
from apscheduler.jobstores.base import BaseJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger as APInterval
from mongoengine import DoesNotExist
from pytz import utc

import brew_view
from bg_utils.mongo.models import Job as BGJob


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
        "func": "brew_view.scheduler:run_job",
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
    request_template.metadata["_bg_job_id"] = job_id

    brew_view.easy_client.create_request(request_template, blocking=True)

    # Be a little careful here as the job could have been removed before this
    job = brew_view.request_scheduler.get_job(job_id)
    if job and getattr(job.trigger, "reschedule_on_finish", False):
        # This essentially resets the timer on this job, which has the effect of
        # making the wait time start whenever the job finishes
        brew_view.request_scheduler.reschedule_job(job_id, trigger=job.trigger)


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
            except BaseException:
                self._logger.exception(
                    'Unable to restore job "%s" -- removing it' % document.id
                )
                failed_jobs.append(document)

        # Remove all the jobs we failed to restore
        if failed_jobs:
            for document in failed_jobs:
                document.delete()

        return jobs
