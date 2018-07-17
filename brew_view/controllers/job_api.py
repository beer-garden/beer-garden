# -*- coding: utf-8 -*-
import logging

from tornado.gen import coroutine

import brew_view
from bg_utils.models import Job
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError


class JobAPI(BaseHandler):
    logger = logging.getLogger(__name__)
    parser = BeerGardenSchemaParser()

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
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
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
            self.request.decoded_body,
            many=True,
            from_string=True
        )

        for op in operations:
            if op.operation == 'update':
                if op.path == '/status':
                    if str(op.value).upper() == 'PAUSED':
                        brew_view.request_scheduler.pause_job(
                            job_id, jobstore='beer_garden'
                        )
                        job.status = 'PAUSED'
                    elif str(op.value).upper() == 'RUNNING':
                        brew_view.request_scheduler.resume_job(
                            job_id, jobstore='beer_garden'
                        )
                        job.status = 'RUNNING'
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
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
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
        brew_view.request_scheduler.remove_job(job_id, jobstore='beer_garden')
        self.set_status(204)
