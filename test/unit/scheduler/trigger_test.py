# -*- coding: utf-8 -*-
from datetime import datetime

import pytest
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from mock import Mock

from brew_view.scheduler.trigger import HoldTrigger


def test_date_trigger():
    trigger = HoldTrigger('date', {})
    assert isinstance(trigger._actual_trigger, DateTrigger)


def test_interval_trigger():
    trigger = HoldTrigger('interval', {})
    assert isinstance(trigger._actual_trigger, IntervalTrigger)


def test_cron_trigger():
    trigger = HoldTrigger('cron', {})
    assert isinstance(trigger._actual_trigger, CronTrigger)


def test_invalid_trigger():
    with pytest.raises(ValueError):
        HoldTrigger('invalid', {})


def test_get_next_fire_time():
    trigger = HoldTrigger('date', {})
    trigger._actual_trigger = Mock()
    now = datetime.now()
    trigger.get_next_fire_time(now, now)
    trigger._actual_trigger.get_next_fire_time.assert_called_with(now, now)