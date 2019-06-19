# -*- coding: utf-8 -*-
import logging

from tornado.gen import coroutine

import brew_view
from bg_utils.mongo.models import Job
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brew_view.scheduler import run_job
from brewtils.errors import ModelValidationError
from brewtils.schemas import JobSchema


class JobAPI(BaseHandler):
    logger = logging.getLogger(__name__)
    parser = MongoParser()

    @authenticated(permissions=[Permissions.JOB_READ])
    def get(self, job_id):
        """
        ---
        summary: Retrieve a specific Job
        parameters:
          - name: job_id
            in: path
            required: true
            description: The ID of the Job
            type: string
        responses:
          200:
            description: Job with the given ID
            schema:
              $ref: '#/definitions/Job'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        document = Job.objects.get(id=job_id)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(self.parser.serialize_job(document, to_string=False))

    @authenticated(permissions=[Permissions.JOB_UPDATE])
    def patch(self, job_id):
        """
        ---
        summary: Pause/Resume a job
        description: |
          The body of the request needs to contain a set of instructions
          detailing the actions to take. Currently the only operation
          supported is `update` with `path` of `/status`.


          You can pause a job with:
          ```JSON
          {
            "operations": [
              { "operation": "update", "path": "/status", "value": "PAUSED" }
            ]
          }
          ```

          And resume it with:
          ```JSON
          {
            "operations": [
                { "operation": "update", "path": "/status", "value": "RUNNING" }
            ]
          }
          ```
        parameters:
          - name: job_id
            in: path
            required: true
            description: The ID of the Job
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for the actions to take
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Job with the given ID
            schema:
              $ref: '#/definitions/Job'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        job = Job.objects.get(id=job_id)
        operations = self.parser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "update":
                if op.path == "/status":
                    if str(op.value).upper() == "PAUSED":
                        brew_view.request_scheduler.pause_job(
                            job_id, jobstore="beer_garden"
                        )
                        job.status = "PAUSED"
                    elif str(op.value).upper() == "RUNNING":
                        brew_view.request_scheduler.resume_job(
                            job_id, jobstore="beer_garden"
                        )
                        job.status = "RUNNING"
                    else:
                        error_msg = "Unsupported status value '%s'" % op.value
                        self.logger.warning(error_msg)
                        raise ModelValidationError(error_msg)
                else:
                    error_msg = "Unsupported path value '%s'" % op.path
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)
            else:
                error_msg = "Unsupported operation '%s'" % op.operation
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        job.save()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(self.parser.serialize_job(job, to_string=False))

    @coroutine
    @authenticated(permissions=[Permissions.JOB_DELETE])
    def delete(self, job_id):
        """
        ---
        summary: Delete a specific Job.
        description: Will remove a specific job. No further executions will occur.
        parameters:
          - name: job_id
            in: path
            required: true
            description: The ID of the Job
            type: string
        responses:
          204:
            description: Job has been successfully deleted.
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        brew_view.request_scheduler.remove_job(job_id, jobstore="beer_garden")
        self.set_status(204)


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
                max_instances=document.max_instances,
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
