# -*- coding: utf-8 -*-
import copy
from datetime import datetime

import pytest

from bg_utils.models import Job, DateTrigger, RequestTemplate


@pytest.fixture
def bad_id():
    """A bad mongo ID"""
    return ''.join(['1' for _ in range(24)])


@pytest.fixture
def ts_epoch():
    """A epoch timestamp."""
    return 1451606400000


@pytest.fixture
def ts_dt(ts_epoch):
    """datetime representation of a timestamp."""
    return datetime.utcfromtimestamp(ts_epoch / 1000)


@pytest.fixture
def request_template_dict():
    """A dictionary representing a request template"""
    return {
        'system': 'system',
        'system_version': '1.0.0',
        'instance_name': 'default',
        'command': 'speak',
        'parameters': {'message': 'hey!'},
        'comment': 'hi!',
        'metadata': {'request': 'stuff'},
    }


@pytest.fixture
def trigger_dict(ts_epoch):
    """A dictionary representing a date trigger."""
    return {
        'run_date': ts_epoch,
        'timezone': 'utc'
    }


@pytest.fixture
def job_dict(ts_epoch, request_template_dict, trigger_dict):
    """A dictionary representation of a job."""
    return {
        'name': 'job_name',
        'trigger_type': 'date',
        'trigger': trigger_dict,
        'request_template': request_template_dict,
        'misfire_grace_time': 3,
        'coalesce': True,
        'max_instances': 2,
        'next_run_time': ts_epoch,
    }


@pytest.fixture
def bg_trigger(trigger_dict, ts_dt):
    """A beer-garden trigger object."""
    dict_copy = copy.deepcopy(trigger_dict)
    dict_copy['run_date'] = ts_dt
    return DateTrigger(**dict_copy)


@pytest.fixture
def bg_request_template(request_template_dict):
    """A request template model."""
    return RequestTemplate(**request_template_dict)


@pytest.fixture
def bg_job(job_dict, ts_dt, bg_trigger, bg_request_template):
    """A job model."""
    dict_copy = copy.deepcopy(job_dict)
    dict_copy['next_run_time'] = ts_dt
    dict_copy['trigger'] = bg_trigger
    dict_copy['request_template'] = bg_request_template
    return Job(id='222222222222222222222222', **dict_copy)
