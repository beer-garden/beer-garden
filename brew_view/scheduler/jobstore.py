# -*- coding: utf-8 -*-

from apscheduler.jobstores.base import BaseJobStore
from mongoengine import DoesNotExist
from pytz import utc

from bg_utils.mongo.models import Job as BGJob
from brew_view.scheduler import db_to_scheduler


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
