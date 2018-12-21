# -*- coding: utf-8 -*-
"""Module for the job runner."""
import brew_view


def run_job(job_id, request_template):
    """Spawned by the scheduler, this will kick off a new request.

    This method is meant to be run in a separate process.

    Args:
        job_id: The Beer-Garden job ID that triggered this event.
        request_template: Request template specified by the job.
    """
    request_template.metadata["_bg_job_id"] = job_id
    brew_view.easy_client.create_request(request_template)
