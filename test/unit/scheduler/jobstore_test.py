# -*- coding: utf-8 -*-

import pytest
from apscheduler.job import Job as APJob
from apscheduler.triggers.date import DateTrigger
from mock import patch
from pytz import utc

from bg_utils.mongo.models import Job


@pytest.fixture(autouse=True)
def drop_systems(app):
    Job.drop_collection()


def test_lookup_nonexistent_job(jobstore, bad_id):
    assert jobstore.lookup_job(bad_id) is None


def test_lookup_job(jobstore, mongo_job):
    mongo_job.save()
    assert jobstore.lookup_job(str(mongo_job.id)) is not None


def test_get_all_jobs(jobstore, mongo_job):
    assert len(jobstore.get_all_jobs()) == 0
    mongo_job.save()
    assert len(jobstore.get_all_jobs()) == 1


def test_lookup_job_state(jobstore, mongo_job):
    mongo_job.save()
    apjob = jobstore.lookup_job(str(mongo_job.id))
    assert isinstance(apjob, APJob)
    state = apjob.__getstate__()
    assert state["id"] == mongo_job.id
    assert state["func"] == "brew_view.scheduler.runner:run_job"
    assert state["executor"] == "default"
    assert state["args"] == ()
    assert state["kwargs"] == {
        "request_template": mongo_job.request_template,
        "job_id": str(mongo_job.id),
    }
    assert state["name"] == mongo_job.name
    assert state["misfire_grace_time"] == mongo_job.misfire_grace_time
    assert state["coalesce"] == mongo_job.coalesce
    assert state["max_instances"] == 3
    assert state["next_run_time"] == utc.localize(mongo_job.next_run_time)

    assert isinstance(state["trigger"], DateTrigger)


def test_get_due_jobs(jobstore, ts_dt, mongo_job):
    now = utc.localize(ts_dt)
    assert jobstore.get_due_jobs(now) == []

    mongo_job.save()
    assert len(jobstore.get_due_jobs(now)) == 1


def test_get_due_jobs_invalid_job(jobstore, mongo_job):
    mongo_job.save()
    with patch("brew_view.scheduler.jobstore.db_to_scheduler") as convert_mock:
        convert_mock.side_effect = ValueError
        assert len(jobstore.get_all_jobs()) == 0


def test_add_job(jobstore, ap_job, mongo_job):
    mongo_job.save()
    jobstore.add_job(ap_job)
    assert len(jobstore.get_all_jobs()) == 1


def test_remove_job(jobstore, mongo_job):
    mongo_job.save()
    jobstore.remove_job(mongo_job.id)
    assert jobstore.lookup_job(mongo_job.id) is None


def get_next_run_time(jobstore, mongo_job):
    assert jobstore.get_next_run_time() is None

    mongo_job.save()
    assert jobstore.get_next_run_time == utc.localize(mongo_job.next_run_time)
