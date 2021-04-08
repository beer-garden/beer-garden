# -*- coding: utf-8 -*-
import threading

import pytest
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from watchdog.events import FileSystemEvent
from mock import Mock
from pytz import utc

import beer_garden
from beer_garden.scheduler import run_job, MixedScheduler
from brewtils.models import RequestTemplate


@pytest.fixture
def scheduler(jobstore):
    job_stores = {"beer_garden": jobstore}
    executors = {"default": APThreadPoolExecutor(1)}
    job_defaults = {"coalesce": True, "max_instances": 3}
    interval_config = {
        "jobstores": job_stores,
        "executors": executors,
        "job_defaults": job_defaults,
        "timezone": utc,
    }

    return MixedScheduler(interval_config=interval_config)


@pytest.fixture
def trigger_event():
    return FileSystemEvent("my/test/path.txt")


@pytest.fixture
def trigger_template():
    request_dict = {
        "system": "system",
        "system_version": "1.0.0",
        "instance_name": "default",
        "namespace": "ns",
        "command": "speak",
        "command_type": "ACTION",
        "parameters": {"message": "Hello {event/src_path}!"},
        "comment": "hi!",
        "metadata": {"request": "stuff"},
        "output_type": "STRING",
    }
    return RequestTemplate(**request_dict)


class TestRunJob(object):
    def test_run_job(self, monkeypatch, scheduler, bg_request_template):
        router_mock = Mock()
        monkeypatch.setattr(beer_garden.scheduler, "beer_garden.router.route", router_mock)

        event_mock = Mock()
        monkeypatch.setattr(threading, "Event", event_mock)

        app_mock = Mock(scheduler=scheduler)
        monkeypatch.setattr(beer_garden, "application", app_mock)

        run_job("job_id", bg_request_template)

        created_request = router_mock.call_args[0][0]
        assert created_request.metadata["_bg_job_id"] == "job_id"

    def test_request_injection(
        self, monkeypatch, scheduler, trigger_template, trigger_event
    ):
        router_mock = Mock()
        monkeypatch.setattr(beer_garden.scheduler, "beer_garden.router.route", router_mock)

        event_mock = Mock()
        monkeypatch.setattr(threading, "Event", event_mock)

        app_mock = Mock(scheduler=scheduler)
        monkeypatch.setattr(beer_garden, "application", app_mock)

        run_job("job_id", trigger_template, event=trigger_event)

        created_request = router_mock.call_args[0][0]
        assert created_request.parameters["message"] == "Hello my/test/path.txt!"
