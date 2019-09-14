# -*- coding: utf-8 -*-
import copy

import pytest

from beer_garden.bg_utils.mongo.models import DateTrigger


@pytest.fixture
def trigger_dict(ts_epoch):
    """A dictionary representing a date trigger."""
    return {"run_date": ts_epoch, "timezone": "utc"}


@pytest.fixture
def bg_trigger(trigger_dict, ts_dt):
    """A beer-garden trigger object."""
    dict_copy = copy.deepcopy(trigger_dict)
    dict_copy["run_date"] = ts_dt
    return DateTrigger(**dict_copy)
