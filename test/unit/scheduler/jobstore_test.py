# -*- coding: utf-8 -*-
from apscheduler.triggers.date import DateTrigger
from mock import patch
from pytz import utc
from apscheduler.job import Job as APJob


def test_lookup_nonexistent_job(jobstore, bad_id):
    assert jobstore.lookup_job(bad_id) is None


def test_lookup_job(jobstore, bg_job):
    bg_job.save()
    assert jobstore.lookup_job(str(bg_job.id)) is not None


def test_get_all_jobs(jobstore, bg_job):
    assert len(jobstore.get_all_jobs()) == 0
    bg_job.save()
    assert len(jobstore.get_all_jobs()) == 1


def test_lookup_job_state(jobstore, bg_job):
    bg_job.save()
    apjob = jobstore.lookup_job(str(bg_job.id))
    assert isinstance(apjob, APJob)
    state = apjob.__getstate__()
    assert state['id'] == bg_job.id
    assert state['func'] == 'brew_view.scheduler.runner:run_job'
    assert state['executor'] == 'default'
    assert state['args'] == ()
    assert state['kwargs'] == {'request_template': bg_job.request_template}
    assert state['name'] == bg_job.name
    assert state['misfire_grace_time'] == bg_job.misfire_grace_time
    assert state['coalesce'] == bg_job.coalesce
    assert state['max_instances'] == bg_job.max_instances
    assert state['next_run_time'] == utc.localize(bg_job.next_run_time)

    assert isinstance(state['trigger'], DateTrigger)


def test_get_due_jobs(jobstore, ts_dt, bg_job):
    now = utc.localize(ts_dt)
    assert jobstore.get_due_jobs(now) == []

    bg_job.save()
    assert len(jobstore.get_due_jobs(now)) == 1


def test_get_due_jobs_invalid_job(jobstore, bg_job):
    bg_job.save()
    with patch('brew_view.scheduler.jobstore.db_to_scheduler') as convert_mock:
        convert_mock.side_effect = ValueError
        assert len(jobstore.get_all_jobs()) == 0


def test_add_job(jobstore, ap_job, bg_job):
    bg_job.save()
    jobstore.add_job(ap_job)
    assert len(jobstore.get_all_jobs()) == 1


def test_remvove_job(jobstore, bg_job):
    bg_job.save()
    jobstore.remove_job(bg_job.id)


def get_next_run_time(jobstore, bg_job):
    assert jobstore.get_next_run_time() is None

    bg_job.save()
    assert jobstore.get_next_run_time == utc.localize(bg_job.next_run_time)
