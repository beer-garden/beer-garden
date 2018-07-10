# -*- coding: utf-8 -*-
import copy
import json
from datetime import datetime

from mock import patch

from bg_utils.models import Job, DateTrigger, RequestTemplate
from . import TestHandlerBase


class JobListAPITest(TestHandlerBase):

    def setUp(self):
        self.ts_epoch = 1451606400000
        self.ts_dt = datetime(2016, 1, 1)
        self.job_dict = {
            'name': 'job_name',
            'trigger_type': 'date',
            'trigger': {
                'run_date': self.ts_epoch,
                'timezone': 'utc',
            },
            'request_template': {
                'system': 'system',
                'system_version': '1.0.0',
                'instance_name': 'default',
                'command': 'speak',
                'parameters': {'message': 'hey!'},
                'comment': 'hi!',
                'metadata': {'request': 'stuff'},
            },
            'misfire_grace_time': 3,
            'coalesce': True,
            'next_run_time': self.ts_epoch,
            'success_count': 0,
            'error_count': 0,
        }
        db_dict = copy.deepcopy(self.job_dict)
        db_dict['request_template'] = RequestTemplate(**db_dict['request_template'])
        db_dict['trigger']['run_date'] = self.ts_dt
        db_dict['trigger'] = DateTrigger(**db_dict['trigger'])
        db_dict['next_run_time'] = self.ts_dt
        self.job = Job(**db_dict)
        super(JobListAPITest, self).setUp()

    def tearDown(self):
        Job.objects.delete()

    def test_get(self):
        self.job.save()
        self.job_dict['id'] = str(self.job.id)
        response = self.fetch('/api/v1/jobs')
        self.assertEqual(200, response.code)
        self.assertEqual(json.loads(response.body.decode('utf-8')), [self.job_dict])

    def test_get_with_filter_param(self):
        self.job.save()
        self.job_dict['id'] = str(self.job.id)

        response = self.fetch('/api/v1/jobs?name=DOES_NOT_EXIST')
        self.assertEqual(200, response.code)
        self.assertEqual(json.loads(response.body.decode('utf-8')), [])

        response = self.fetch('/api/v1/jobs?name=job_name')
        self.assertEqual(200, response.code)
        self.assertEqual(
            json.loads(response.body.decode('utf-8')),
            [self.job_dict]
        )

    @patch('brew_view.request_scheduler')
    def test_post(self, scheduler_mock):
        body = json.dumps(self.job_dict)
        self.job_dict['id'] = None
        response = self.fetch('/api/v1/jobs', method='POST', body=body)
        self.assertEqual(response.code, 201)
        data_without_id = json.loads(response.body.decode('utf-8'))
        data_without_id['id'] = None
        self.assertEqual(
            data_without_id,
            self.job_dict
        )
        self.assertEqual(scheduler_mock.add_job.call_count, 1)
