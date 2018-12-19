# -*- coding: utf-8 -*-
"""scheduler module methods."""
from apscheduler.job import Job as APJob
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from pytz import utc


def construct_trigger(trigger_type, bg_trigger):
    """Construct an apscheduler trigger based on type and mongo document."""
    trigger_type = trigger_type
    trigger_kwargs = bg_trigger.get_scheduler_kwargs()
    if trigger_type == "date":
        return DateTrigger(**trigger_kwargs)
    elif trigger_type == "interval":
        return IntervalTrigger(**trigger_kwargs)
    elif trigger_type == "cron":
        return CronTrigger(**trigger_kwargs)
    else:
        raise ValueError("Invalid trigger type %s" % trigger_type)


def db_to_scheduler(document, scheduler, alias="beer_garden"):
    """Convert a database job to a scheduler's job."""
    job = APJob.__new__(APJob)
    if document.next_run_time:
        next_run_time = utc.localize(document.next_run_time)
    else:
        next_run_time = None
    state = {
        "id": document.id,
        "func": "brew_view.scheduler.runner:run_job",
        "trigger": construct_trigger(document.trigger_type, document.trigger),
        "executor": "default",
        "args": (),
        "kwargs": {
            "request_template": document.request_template,
            "job_id": str(document.id),
        },
        "name": document.name,
        "misfire_grace_time": document.misfire_grace_time,
        "coalesce": document.coalesce,
        "max_instances": 3,
        "next_run_time": next_run_time,
    }
    job.__setstate__(state)
    job._scheduler = scheduler
    job._jobstore_alias = alias
    return job
