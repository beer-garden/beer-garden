# -*- coding: utf-8 -*-
import logging
from typing import List, Dict

from apscheduler.triggers.interval import IntervalTrigger as APInterval
from brewtils.models import Job

import beer_garden
import beer_garden.db.api as db
from beer_garden.requests import process_request

logger = logging.getLogger(__name__)


class IntervalTrigger(APInterval):
    """Beergarden implementation of an apscheduler IntervalTrigger"""

    def __init__(self, *args, **kwargs):
        self.reschedule_on_finish = kwargs.pop("reschedule_on_finish", False)
        super(IntervalTrigger, self).__init__(*args, **kwargs)


def run_job(job_id, request_template):
    """Spawned by the scheduler, this will kick off a new request.

    This method is meant to be run in a separate process.

    Args:
        job_id: The Beer-Garden job ID that triggered this event.
        request_template: Request template specified by the job.
    """
    request_template.metadata["_bg_job_id"] = job_id

    # TODO - Possibly allow specifying blocking timeout on the job definition
    # Want to wait for completion here
    request = process_request(request_template, wait_timeout=-1)

    try:
        db_job = db.query_unique(Job, id=job_id)
        if request.status == "ERROR":
            db_job.error_count += 1
        elif request.status == "SUCCESS":
            db_job.success_count += 1
        db.update(db_job)
    except Exception as ex:
        logger.exception(f"Could not update job counts: {ex}")

    # Be a little careful here as the job could have been removed or paused
    job = beer_garden.application.scheduler.get_job(job_id)
    if (
        job
        and job.next_run_time is not None
        and getattr(job.trigger, "reschedule_on_finish", False)
    ):
        # This essentially resets the timer on this job, which has the effect of
        # making the wait time start whenever the job finishes
        beer_garden.application.scheduler.reschedule_job(job_id, trigger=job.trigger)


def get_job(job_id: str) -> Job:
    return db.query_unique(Job, id=job_id)


def get_jobs(filter_params: Dict = None) -> List[Job]:
    return db.query(Job, filter_params=filter_params)


def create_job(job: Job) -> Job:
    """Create a new Job and add it to the scheduler

    Args:
        job: The Job to be added

    Returns:
        The added Job
    """
    # Save first so we have an ID to pass to the scheduler
    job = db.create(job)

    try:
        beer_garden.application.scheduler.add_job(
            run_job,
            None,
            kwargs={"request_template": job.request_template, "job_id": str(job.id)},
            name=job.name,
            misfire_grace_time=job.misfire_grace_time,
            coalesce=job.coalesce,
            max_instances=job.max_instances,
            jobstore="beer_garden",
            replace_existing=False,
            id=str(job.id),
        )
    except Exception:
        db.delete(job)
        raise

    return job


def pause_job(job_id: str) -> Job:
    """Pause a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """
    beer_garden.application.scheduler.pause_job(job_id, jobstore="beer_garden")

    job = db.query_unique(Job, id=job_id)
    job.status = "PAUSED"
    job = db.update(job)

    return job


def resume_job(job_id: str) -> Job:
    """Resume a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """
    beer_garden.application.scheduler.resume_job(job_id, jobstore="beer_garden")

    job = db.query_unique(Job, id=job_id)
    job.status = "RUNNING"
    job = db.update(job)

    return job


def remove_job(job_id: str) -> None:
    """Remove a Job

    Args:
        job_id: The Job ID

    Returns:
        None
    """
    # The scheduler takes care of removing the Job from the database
    beer_garden.application.scheduler.remove_job(job_id, jobstore="beer_garden")
