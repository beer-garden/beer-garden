# -*- coding: utf-8 -*-
"""module for controller for /jobs endpoint."""
import logging

import brew_view
from bg_utils.models import Job
from bg_utils.parser import BeerGardenSchemaParser
from tornado.gen import coroutine

from brew_view.base_handler import BaseHandler
from brew_view.job_runner import run_job
from brew_view.scheduler.trigger import HoldTrigger
from brewtils.schemas import JobSchema


class JobListAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    def get(self):
        """
        ---
        summary: Retrieve all Jobs.
        responses:
          200:
            description: Successfully retrieved all systems.
            schema:
              type: array
              items:
                $ref: '#/definitions/Job'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        filter_params = {}
        for key in self.request.arguments.keys():
            if key in JobSchema.get_attribute_names():
                filter_params[key] = self.get_query_argument(key)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(self.parser.serialize_job(
            Job.objects.filter(**filter_params),
            to_string=True,
            many=True
        ))

    @coroutine
    def post(self, *args, **kwargs):
        """
        ---
        summary: Schedules a Job to be run.
        description: Given a job, it will be scheduled to run on the interval
            set in the trigger argument.
        parameters:
          - name: job
            in: body
            description: The Job to create/schedule.
            schema:
              $ref: '#/definitions/Job'
        responses:
          201:
            description: A new job has been created.
            schema:
              $ref: '#/definitions/Job'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        job_model = self.parser.parse_job(
            self.request.decoded_body,
            from_string=True
        )
        trigger = HoldTrigger(job_model.trigger_type, job_model.trigger_args)

        brew_view.scheduler.add_job(
            run_job,
            trigger,
            args=(job_model.request_template, ),
            name=job_model.name,
            misfire_grace_time=job_model.misfire_grace_time,
            coalesce=job_model.coalesce,
            max_instances=job_model.max_instances,
            jobstore='beer_garden',
            replace_existing=False,
            id=job_model.id,
        )

        self.set_status(201)
        self.write(self.parser.serialize_job(job_model, to_string=False))
