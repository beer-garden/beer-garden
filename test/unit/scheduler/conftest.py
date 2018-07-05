# -*- coding: utf-8 -*-
import pytest
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from mock import Mock
from mongoengine import connect
from apscheduler.job import Job as APJob
from pytz import utc

from brew_view import BGJobStore
from brew_view.scheduler.trigger import HoldTrigger


@pytest.fixture
def jobstore():
    """A Beer Garden Job Store."""
    connect('beer_garden', host='mongomock://localhost')
    js = BGJobStore()
    yield js
    js.remove_all_jobs()


@pytest.fixture
def ap_job(bg_job, request_template):
    trigger = HoldTrigger(bg_job.trigger_type, bg_job.trigger_args)
    job_kwargs = {
        'func': Mock(),
        'scheduler': Mock(BaseScheduler, timezone=utc),
        'trigger': trigger,
        'executor': 'default',
        'args': (request_template,),
        'kwargs': {},
        'id': str(bg_job.id),
        'misfire_grace_time': bg_job.misfire_grace_time,
        'coalesce': bg_job.coalesce,
        'name': bg_job.name,
        'max_instances': bg_job.max_instances,
    }
    job_kwargs.setdefault('next_run_time', None)
    return APJob(**job_kwargs)
