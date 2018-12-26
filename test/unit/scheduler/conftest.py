# -*- coding: utf-8 -*-
import pytest
from apscheduler.job import Job as APJob
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.date import DateTrigger
from mock import Mock
from mongoengine import connect
from pytz import utc

from brew_view import BGJobStore


@pytest.fixture
def jobstore():
    """A Beer Garden Job Store."""
    connect("beer_garden", host="mongomock://localhost")
    js = BGJobStore()
    yield js
    js.remove_all_jobs()


@pytest.fixture
def ap_job(mongo_job, bg_request_template):
    job_kwargs = {
        "func": Mock(),
        "scheduler": Mock(BaseScheduler, timezone=utc),
        "trigger": DateTrigger(),
        "executor": "default",
        "args": (),
        "kwargs": {"request_template": bg_request_template},
        "id": str(mongo_job.id),
        "misfire_grace_time": mongo_job.misfire_grace_time,
        "coalesce": mongo_job.coalesce,
        "name": mongo_job.name,
        "max_instances": 3,
    }
    job_kwargs.setdefault("next_run_time", None)
    return APJob(**job_kwargs)
