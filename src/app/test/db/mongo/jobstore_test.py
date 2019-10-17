# -*- coding: utf-8 -*-
import copy

import pytest
from apscheduler.job import Job as APJob
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.date import DateTrigger
from brewtils.test.comparable import assert_request_template_equal
from mock import patch, Mock
from pytz import utc

from beer_garden.db.mongo.models import (
    Job,
    RequestTemplate,
    DateTrigger as MongoDateTrigger,
)


@pytest.fixture
def ap_job(mongo_job, mongo_request_template):
    job_kwargs = {
        "func": Mock(),
        "scheduler": Mock(BaseScheduler, timezone=utc),
        "trigger": DateTrigger(),
        "executor": "default",
        "args": (),
        "kwargs": {"request_template": mongo_request_template},
        "id": str(mongo_job.id),
        "misfire_grace_time": mongo_job.misfire_grace_time,
        "coalesce": mongo_job.coalesce,
        "name": mongo_job.name,
        "max_instances": 3,
    }
    job_kwargs.setdefault("next_run_time", None)
    return APJob(**job_kwargs)


@pytest.fixture
def mongo_date_trigger(date_trigger_dict, ts_dt):
    """A date trigger as a model."""
    dict_copy = copy.deepcopy(date_trigger_dict)
    dict_copy["run_date"] = ts_dt
    return MongoDateTrigger(**dict_copy)


@pytest.fixture
def mongo_request_template(request_template_dict):
    """Request template as a bg model."""
    return RequestTemplate(**request_template_dict)


@pytest.fixture
def mongo_job(job_dict, ts_dt, mongo_request_template, mongo_date_trigger):
    """A job as a model."""
    dict_copy = copy.deepcopy(job_dict)
    dict_copy["next_run_time"] = ts_dt
    dict_copy["trigger"] = mongo_date_trigger
    dict_copy["request_template"] = mongo_request_template
    return Job(**dict_copy)


class TestJobStore(object):
    @pytest.fixture(autouse=True)
    def drop_systems(self, mongo_conn):
        Job.drop_collection()

    def test_lookup_nonexistent_job(self, jobstore, bad_id):
        assert jobstore.lookup_job(bad_id) is None

    def test_lookup_job(self, jobstore, mongo_job):
        mongo_job.save()
        assert jobstore.lookup_job(str(mongo_job.id)) is not None

    def test_get_all_jobs(self, jobstore, mongo_job):
        assert len(jobstore.get_all_jobs()) == 0
        mongo_job.save()
        assert len(jobstore.get_all_jobs()) == 1

    def test_lookup_job_state(self, jobstore, mongo_job, bg_request_template):
        mongo_job.save()
        apjob = jobstore.lookup_job(str(mongo_job.id))
        assert isinstance(apjob, APJob)
        state = apjob.__getstate__()
        assert state["id"] == mongo_job.id
        assert state["func"] == "beer_garden.scheduler:run_job"
        assert state["executor"] == "default"
        assert state["args"] == ()
        assert state["name"] == mongo_job.name
        assert state["misfire_grace_time"] == mongo_job.misfire_grace_time
        assert state["coalesce"] == mongo_job.coalesce
        assert state["max_instances"] == 3
        assert state["next_run_time"] == utc.localize(mongo_job.next_run_time)
        assert state["kwargs"]["job_id"] == str(mongo_job.id)
        assert_request_template_equal(
            state["kwargs"]["request_template"], bg_request_template
        )

        assert isinstance(state["trigger"], DateTrigger)

    def test_get_due_jobs(self, jobstore, ts_dt, mongo_job):
        now = utc.localize(ts_dt)
        assert jobstore.get_due_jobs(now) == []

        mongo_job.save()
        assert len(jobstore.get_due_jobs(now)) == 1

    def test_get_due_jobs_invalid_job(self, jobstore, mongo_job):
        mongo_job.save()
        with patch("beer_garden.db.mongo.jobstore.db_to_scheduler") as convert_mock:
            convert_mock.side_effect = ValueError
            assert len(jobstore.get_all_jobs()) == 0

    def test_add_job(self, jobstore, ap_job, mongo_job):
        mongo_job.save()
        jobstore.add_job(ap_job)
        assert len(jobstore.get_all_jobs()) == 1

    def test_remove_job(self, jobstore, mongo_job):
        mongo_job.save()
        jobstore.remove_job(mongo_job.id)
        assert jobstore.lookup_job(mongo_job.id) is None

    def test_get_next_run_time(self, jobstore, mongo_job):
        assert jobstore.get_next_run_time() is None

        mongo_job.save()
        assert jobstore.get_next_run_time() == utc.localize(mongo_job.next_run_time)
