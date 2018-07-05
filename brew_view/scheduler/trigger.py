# -*- coding: utf-8 -*-
import logging

from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger


class HoldTrigger(BaseTrigger):
    logger = logging.getLogger(__name__)

    def __init__(self, trigger_type, trigger_args):
        self.trigger_type = trigger_type
        self.trigger_args = trigger_args
        if trigger_type == 'date':
            self._actual_trigger = DateTrigger(**self.trigger_args)
        elif trigger_type == 'interval':
            self._actual_trigger = IntervalTrigger(**self.trigger_args)
        elif trigger_type == 'cron':
            self._actual_trigger = CronTrigger(**self.trigger_args)
        else:
            raise ValueError('Invalid trigger type %s' % self.trigger_type)

        self.__slots__ = self._actual_trigger.__slots__

    def get_next_fire_time(self, previous_fire_time, now):
        return self._actual_trigger.get_next_fire_time(previous_fire_time, now)

    def __getattr__(self, item):
        return getattr(self._actual_trigger, item)
