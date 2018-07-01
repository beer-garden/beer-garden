# -*- coding: utf-8 -*-
from tornado.gen import coroutine

import brew_view
from bg_utils.models import Job
from brew_view.base_handler import BaseHandler

# TODO:
# * Swagger documentation
# * implement patch
# * Implement get

class JobAPI(BaseHandler):

    @coroutine
    def delete(self, job_id):
        job = Job.object.get(id=job_id)
        brew_view.scheduler.remove_job(job_id, jobstore='mongo')
        job.delete()
        self.set_status(204)
