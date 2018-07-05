# -*- coding: utf-8 -*-
import logging

from tornado.gen import coroutine

import brew_view
from bg_utils.models import Job
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.base_handler import BaseHandler

# TODO:
# * implement patch


class JobAPI(BaseHandler):
    logger = logging.getLogger(__name__)
    parser = BeerGardenSchemaParser()

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
        self.write(self.parser.serialize_job(document, to_string=False))

    @coroutine
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
        brew_view.scheduler.remove_job(job_id, jobstore='beer_garden')
        self.set_status(204)
