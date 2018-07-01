# -*- coding: utf-8 -*-
import logging

import brew_view
from bg_utils.models import Job
from bg_utils.parser import BeerGardenSchemaParser
from tornado.gen import coroutine

from brew_view.base_handler import BaseHandler
from brew_view.job_runner import run_job
from brewtils.schemas import JobSchema

# TODO:
# * swagger documentation
# * Better error handling for job scheduling

class JobListAPI(BaseHandler):
    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    def get(self):
        filter_params = {}
        for key in self.request.arguments.keys():
            if key in JobSchema.get_attribute_names():
                filter_params[key] = self.get_query_argument(key)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(self.parser.serialize_job(
            Job.objects.filter(**filter_params),
            to_string=True, many=True
        ))

    @coroutine
    def post(self, *args, **kwargs):
        job_model = self.parser.parse_job(
            self.request.decoded_body, from_string=True
        )
        job_model.save()

        job = brew_view.scheduler.add_job(
            run_job,
            job_model.trigger_type,
            args=job_model.request_payload,
            name=job_model.name,
            misfire_grace_time=job_model.misfire_grace_time,
            coalesce=job_model.coalesce,
            max_instances=job_model.max_instances,
            jobstore='mongo',
            replace_existing=False,
            id=str(job_model.id),
            **job_model.trigger_args
        )

        self.set_status(201)
        self.write(self.parser.serialize_job(job, to_string=False))
