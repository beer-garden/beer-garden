# -*- coding: utf-8 -*-
import logging
from typing import Dict, List

from apscheduler.triggers.interval import IntervalTrigger as APInterval

from beer_garden.events import publish_event
from brewtils.models import Job, Events, Event

import beer_garden
import beer_garden.config as config
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
    # We now use the events to update the scheduler, no longer have to wait
    process_request(request_template)


def get_job(job_id: str) -> Job:
    return db.query_unique(Job, id=job_id)


def get_jobs(filter_params: Dict = None) -> List[Job]:
    return db.query(Job, filter_params=filter_params)


@publish_event(Events.JOB_CREATED)
def create_job(job: Job) -> Job:
    """Create a new Job and add it to the scheduler

    Args:
        job: The Job to be added

    Returns:
        The added Job
    """
    # Save first so we have an ID to pass to the scheduler
    job = db.create(job)

    return job


@publish_event(Events.JOB_PAUSED)
def pause_job(job_id: str) -> Job:
    """Pause a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """

    job = db.query_unique(Job, id=job_id)
    job.status = "PAUSED"
    job = db.update(job)

    return job


@publish_event(Events.JOB_RESUMED)
def resume_job(job_id: str) -> Job:
    """Resume a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job definition
    """

    job = db.query_unique(Job, id=job_id)
    job.status = "RUNNING"
    job = db.update(job)

    return job


@publish_event(Events.JOB_DELETED)
def remove_job(job_id: str) -> None:
    """Remove a Job

    Args:
        job_id: The Job ID

    Returns:
        The Job ID
    """
    # The scheduler takes care of removing the Job from the database
    return db.query_unique(Job, id=job_id)


def handle_event(event: Event) -> None:
    """Handle JOB events

    When creating or updating a job, make sure to mark as local first.

    BG should only handle events that are designated for the local environment. If BG
    triggers off a non-local JOB, then the JOB could be ran twice.

    Args:
        event: The event to handle
    """
    if (
        event.name == Events.REQUEST_COMPLETED.name
        and event.payload.metadata
        and "_bg_job_id" in event.payload.metadata
    ):

        try:
            db_job = db.query_unique(Job, id=event.payload.metadata["_bg_job_id"])
            if db_job:
                if event.payload.status == "ERROR":
                    db_job.error_count += 1
                elif event.payload.status == "SUCCESS":
                    db_job.success_count += 1
                db.update(db_job)
            else:
                # If the job is not in the database, don't proceed to update scheduler
                return
        except Exception as ex:
            logger.exception(f"Could not update job counts: {ex}")

        # Be a little careful here as the job could have been removed or paused
        job = beer_garden.application.scheduler.get_job(
            event.payload.metadata["_bg_job_id"]
        )
        if (
            job
            and job.next_run_time is not None
            and getattr(job.trigger, "reschedule_on_finish", False)
        ):
            # This essentially resets the timer on this job, which has the effect of
            # making the wait time start whenever the job finishes
            beer_garden.application.scheduler.reschedule_job(
                event.payload.metadata["_bg_job_id"], trigger=job.trigger
            )

    elif event.garden == config.get("garden.name"):

        if event.name == Events.JOB_CREATED.name:
            try:
                beer_garden.application.scheduler.add_job(
                    run_job,
                    None,
                    kwargs={
                        "request_template": event.payload.request_template,
                        "job_id": str(event.payload.id),
                    },
                    name=event.payload.name,
                    misfire_grace_time=event.payload.misfire_grace_time,
                    coalesce=event.payload.coalesce,
                    max_instances=event.payload.max_instances,
                    jobstore="beer_garden",
                    replace_existing=False,
                    id=str(event.payload.id),
                )
            except Exception:
                db.delete(event.payload)
                raise

        elif event.name == Events.JOB_PAUSED.name:
            beer_garden.application.scheduler.pause_job(
                event.payload.id, jobstore="beer_garden"
            )
        elif event.name == Events.JOB_RESUMED.name:
            beer_garden.application.scheduler.resume_job(
                event.payload.id, jobstore="beer_garden"
            )
        elif event.name == Events.JOB_DELETED.name:
            beer_garden.application.scheduler.remove_job(
                event.payload.id, jobstore="beer_garden"
            )
