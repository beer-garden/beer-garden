# -*- coding: utf-8 -*-
import brew_view


def run_job(request_template):
    """Spawned by the scheduler, this will kick off a new request.

    This method is meant to be run in a separate process.

    Args:
        request_template: Request template specified by the job.
    """
    brew_view.easy_client.create_request(request_template)
