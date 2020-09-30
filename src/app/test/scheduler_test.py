# -*- coding: utf-8 -*-
import threading

import pytest
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from mock import Mock
from pytz import utc

import beer_garden
from beer_garden.scheduler import run_job


@pytest.fixture
def scheduler(jobstore):
    job_stores = {"beer_garden": jobstore}
    executors = {"default": APThreadPoolExecutor(1)}
    job_defaults = {"coalesce": True, "max_instances": 3}

    return BackgroundScheduler(
        jobstores=job_stores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=utc,
    )


class TestRunJob(object):
    def test_run_job(self, monkeypatch, scheduler, bg_request_template):
        process_mock = Mock()
        monkeypatch.setattr(beer_garden.scheduler, "process_request", process_mock)

        event_mock = Mock()
        monkeypatch.setattr(threading, "Event", event_mock)

        app_mock = Mock(scheduler=scheduler)
        monkeypatch.setattr(beer_garden, "application", app_mock)

        run_job("job_id", bg_request_template)

        created_request = process_mock.call_args[0][0]
        assert created_request.metadata["_bg_job_id"] == "job_id"
