# -*- coding: utf-8 -*-

from apscheduler.jobstores.base import BaseJobStore
from apscheduler.job import Job as APJob
from mongoengine import DoesNotExist
from pytz import utc

from bg_utils.models import Job as BGJob
from brew_view.scheduler.trigger import HoldTrigger


class BGJobStore(BaseJobStore):

    def lookup_job(self, job_id):
        try:
            document = BGJob.objects.get(id=job_id)
            return self._reconstitue_job(document)
        except DoesNotExist:
            return None

    def get_due_jobs(self, now):
        return self._get_jobs({'next_run_time__lte': now})

    def get_next_run_time(self):
        try:
            document = BGJob.objects(
                next_run_time__ne=None
            ).order_by(
                'next_run_time'
            ).fields(next_run_time=1).first()

            if document:
                return utc.localize(document.next_run_time)
        except DoesNotExist:
            return None

    def get_all_jobs(self):
        return self._get_jobs({})

    def add_job(self, job):
        bg_job = BGJob(
            name=job.name,
            trigger_type=job.trigger.trigger_type,
            trigger_args=job.trigger.trigger_args,
            request_template=job.args[0],
            misfire_grace_time=job.misfire_grace_time,
            coalesce=job.coalesce,
            max_instances=job.max_instances,
            next_run_time=job.next_run_time,
        )
        bg_job.save()

    def update_job(self, job):
        document = BGJob.objects.get(id=job.id)
        for key, value in job.__getstate__().items():
            setattr(document, key, value)

        document.save()

    def remove_job(self, job_id):
        BGJob.objects.get(id=job_id).delete()

    def remove_all_jobs(self):
        BGJob.objects.delete()

    def _get_jobs(self, conditions):
        jobs = []
        failed_jobs = []
        for document in BGJob.objects(**conditions).order_by('next_run_time'):
            try:
                jobs.append(self._reconstitue_job(document))
            except BaseException:
                self._logger.exception(
                    'Unable to restore job "%s" -- removing it' % document.id
                )
                failed_jobs.append(document)

        # Remove all the jobs we failed to restore
        if failed_jobs:
            for job in failed_jobs:
                job.delete()

        return jobs

    def _reconstitue_job(self, document):
        job = APJob.__new__(APJob)
        if document.next_run_time:
            next_run_time = utc.localize(document.next_run_time)
        else:
            next_run_time = None
        state = {
            'id': document.id,
            'func': 'brew_view.scheduler.runner:run_job',
            'trigger': HoldTrigger(document.trigger_type, document.trigger_args),
            'executor': 'default',
            'args': [document.request_template],
            'kwargs': {},
            'name': document.name,
            'misfire_grace_time': document.misfire_grace_time,
            'coalesce': document.coalesce,
            'max_instances': document.max_instances,
            'next_run_time': next_run_time,
        }
        job.__setstate__(state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job
