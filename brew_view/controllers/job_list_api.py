# -*- coding: utf-8 -*-
"""module for controller for /jobs endpoint."""
import logging

from tornado.gen import coroutine

import brew_view
from bg_utils.mongo.models import Job
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brew_view.scheduler.runner import run_job
from brewtils.schemas import JobSchema


class JobListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.JOB_READ])
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

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            self.parser.serialize_job(
                Job.objects.filter(**filter_params), to_string=True, many=True
            )
        )

    @coroutine
    @authenticated(permissions=[Permissions.JOB_CREATE])
    def post(self):
        """
        ---
        summary: Schedules a Job to be run.
        description: |
          Given a job, it will be scheduled to run on the interval
          set in the trigger argument.
        parameters:
          - name: job
            in: body
            description: The Job to create/schedule
            schema:
              $ref: '#/definitions/Job'
        responses:
          201:
            description: A new job has been created
            schema:
              $ref: '#/definitions/Job'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        document = self.parser.parse_job(self.request.decoded_body, from_string=True)
        # We have to save here, because we need an ID to pass
        # to the scheduler.
        document.save()

        try:
            brew_view.request_scheduler.add_job(
                run_job,
                None,
                kwargs={
                    "request_template": document.request_template,
                    "job_id": str(document.id),
                },
                name=document.name,
                misfire_grace_time=document.misfire_grace_time,
                coalesce=document.coalesce,
                max_instances=3,
                jobstore="beer_garden",
                replace_existing=False,
                id=str(document.id),
            )
        except Exception:
            document.delete()
            raise

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(self.parser.serialize_job(document, to_string=False))
