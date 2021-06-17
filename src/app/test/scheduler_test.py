# -*- coding: utf-8 -*-

import pytest
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from brewtils.models import RequestTemplate
from pytz import utc
from watchdog.events import FileSystemEvent

from beer_garden.scheduler import MixedScheduler


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
