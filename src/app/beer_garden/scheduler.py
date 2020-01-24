# -*- coding: utf-8 -*-
import logging
from typing import List, Dict

from apscheduler.triggers.interval import IntervalTrigger as APInterval

from beer_garden.errors import RoutingRequestException
from beer_garden.router import Route_Type
from brewtils.errors import ModelValidationError
from brewtils.models import Job

import beer_garden
import beer_garden.db.api as db
from beer_garden.requests import process_request
from brewtils.schema_parser import SchemaParser

logger = logging.getLogger(__name__)


class IntervalTrigger(APInterval):
    """Beergarden implementation of an apscheduler IntervalTrigger"""

    def __init__(self, *args, **kwargs):
        self.reschedule_on_finish = kwargs.pop("reschedule_on_finish", False)
        super(IntervalTrigger, self).__init__(*args, **kwargs)


def route_request(
    brewtils_obj=None, obj_id: str = None, route_type: Route_Type = None, **kwargs
):
    if route_type is Route_Type.CREATE:
        if brewtils_obj is None:
            raise RoutingRequestException(
                "An Object is required to route CREATE request for Scheduler"
            )
        return create_job(SchemaParser.parse_job(brewtils_obj, from_string=False))
    elif route_type is Route_Type.READ:
        if obj_id:
            return get_job(obj_id)
        elif kwargs.get("filter_params", None) is not None:
            return get_jobs(kwargs.get("filter_params", None))
        else:
            raise RoutingRequestException(
                "An identifier OR Filter Params are required to route READ request for "
                "Scheduler"
            )
    elif route_type is Route_Type.UPDATE:
        if obj_id is None or brewtils_obj is None:
            raise RoutingRequestException(
                "An identifier and Object are required to route UPDATE request for Scheduler"
            )
        operations = SchemaParser.parse_patch(
            brewtils_obj, many=True, from_string=False
        )

        for op in operations:
            if op.operation == "update":
                if op.path == "/status":
                    if str(op.value).upper() == "PAUSED":
                        response = pause_job(obj_id)
                    elif str(op.value).upper() == "RUNNING":
                        response = resume_job(obj_id)
                    else:
                        raise ModelValidationError(
                            f"Unsupported status value '{op.value}'"
                        )
                else:
                    raise ModelValidationError(f"Unsupported path value '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    elif route_type is Route_Type.DELETE:
        if obj_id is None:
            raise RoutingRequestException(
                "An identifier is required to route DELETE request for Scheduler"
            )
        return remove_job(obj_id)
    else:
        raise RoutingRequestException(
            "%s Route for Scheduler does not exist" % route_type.value
        )


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
