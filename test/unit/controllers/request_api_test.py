import copy
import datetime
import json

from mock import Mock

from bg_utils.models import Request, Job, RequestTemplate, DateTrigger
from . import TestHandlerBase


class RequestAPITest(TestHandlerBase):

    def setUp(self):
        self.request_mock = Mock()

        self.ts_epoch = 1451606400000
        self.ts_dt = datetime.datetime(2016, 1, 1)
        self.request_dict = {
            'children': [],
            'parent': None,
            'system': 'system_name',
            'system_version': '0.0.1',
            'instance_name': 'default',
            'command': 'say',
            'id': '58542eb571afd47ead90d25f',
            'parameters': {},
            'comment': 'bye!',
            'output': 'nested output',
            'output_type': 'STRING',
            'status': 'IN_PROGRESS',
            'command_type': 'ACTION',
            'created_at': self.ts_epoch,
            'updated_at': self.ts_epoch,
            'error_class': None,
            'metadata': {},
            'has_parent': True,
        }
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

        db_dict = copy.deepcopy(self.request_dict)
        db_dict['created_at'] = self.ts_dt
        db_dict['updated_at'] = self.ts_dt
        self.request = Request(**db_dict)

        super(RequestAPITest, self).setUp()

    def tearDown(self):
        Request.objects.delete()
        Job.objects.delete()

    def test_get(self):
        self.request.save()
        response = self.fetch('/api/v1/requests/' + str(self.request.id))
        self.assertEqual(200, response.code)
        data = json.loads(response.body.decode('utf-8'))
        data.pop('updated_at')
        self.request_dict.pop('updated_at')
        self.assertEqual(self.request_dict, data)

    def test_patch_replace_duplicate(self):
        self.request.status = 'SUCCESS'
        self.request.output = 'output'
        self.request.save()
        body = json.dumps({
                "operations": [
                        {
                            "operation": "replace",
                            "path": "/output",
                            "value": "output"
                        },
                        {
                            "operation": "replace",
                            "path": "/status",
                            "value": "SUCCESS"
                        },
                ]
        })

        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.assertEqual(200, response.code)

        self.request.reload()
        self.assertEqual("SUCCESS", self.request.status)
        self.assertEqual("output", self.request.output)

    def test_patch_replace_status(self):
        self.request.save()
        body = json.dumps({"operations": [{"operation": "replace", "path": "/status",
                                           "value": "SUCCESS"}]})

        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.assertEqual(200, response.code)
        self.request.reload()
        self.assertEqual("SUCCESS", self.request.status)

    def test_patch_replace_output(self):
        self.request.output = 'old_output_but_not_done_with_progress'
        self.request.save()
        body = json.dumps({"operations": [{"operation": "replace", "path": "/output",
                                           "value": "output"}]})

        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.assertEqual(200, response.code)
        self.request.reload()
        self.assertEqual("output", self.request.output)

    def test_patch_replace_error_class(self):
        self.request.error_class = 'Klazz1'
        body = json.dumps({"operations": [{"operation": "replace", "path": "/error_class",
                                           "value": "error"}]})
        self.request.save()

        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.request.reload()
        self.assertEqual(200, response.code)
        self.assertEqual("error", self.request.error_class)

    def test_patch_replace_bad_status(self):
        self.request.save()
        body = json.dumps({"operations": [{"operation": "replace", "path": "/status",
                                           "value": "bad"}]})
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.assertGreaterEqual(response.code, 400)

    def test_patch_update_output_for_complete_request(self):
        self.request.status = 'SUCCESS'
        self.request.output = 'old_value'
        self.request.save()
        body = json.dumps({"operations": [{"operation": "replace", "path": "/output",
                                           "value": "shouldnt work"}]})
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.request.reload()
        self.assertGreaterEqual(response.code, 400)
        self.assertEqual(self.request.output, 'old_value')

    def test_patch_no_system(self):
        good_id_does_not_exist = ''.join('1' for _ in range(24))
        response = self.fetch(
            '/api/v1/requests/' + good_id_does_not_exist,
            method='PATCH',
            body='{"operations": [{"operation": "fake"}]}',
            headers={'content-type': 'application/json'}
        )
        self.assertEqual(response.code, 404)

    def test_patch_replace_bad_path(self):
        self.request.save()
        body = json.dumps({"operations": [{"operation": "replace", "path": "/bad",
                                           "value": "error"}]})
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'}
        )
        self.assertGreaterEqual(response.code, 400)

    def test_patch_bad_operation(self):
        self.request.save()
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body='{"operations": [{"operation": "fake"}]}',
            headers={'content-type': 'application/json'}
        )
        self.assertGreaterEqual(response.code, 400)

    def test_prometheus_endpoint(self):
        handler = self.app.find_handler(request=Mock(path='/api/v1/requests'))
        c = handler.handler_class(
            self.app,
            Mock(path='/api/v1/requests/111111111111111111111111')
        )
        assert c.prometheus_endpoint == '/api/v1/requests/<ID>'

    def test_update_job_numbers(self):
        self.job.save()
        self.request.metadata['_bg_job_id'] = str(self.job.id)
        self.request.save()
        body = json.dumps(
            {
                "operations": [
                    {
                        "operation": "replace",
                        "path": "/status",
                        "value": "SUCCESS"
                    }
                ]
            }
        )
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'},
        )
        self.assertEqual(response.code, 200)
        self.job.reload()
        self.assertEqual(self.job.success_count, 1)
        self.assertEqual(self.job.error_count, 0)

    def test_update_job_numbers_error(self):
        self.job.save()
        self.request.metadata['_bg_job_id'] = str(self.job.id)
        self.request.save()
        body = json.dumps(
            {
                "operations": [
                    {
                        "operation": "replace",
                        "path": "/status",
                        "value": "ERROR"
                    }
                ]
            }
        )
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'},
        )
        self.assertEqual(response.code, 200)
        self.job.reload()
        self.assertEqual(self.job.success_count, 0)
        self.assertEqual(self.job.error_count, 1)

    def test_update_job_invalid_id(self):
        self.request.metadata['_bg_job_id'] = ''.join(['1' for _ in range(24)])
        self.request.save()
        body = json.dumps(
            {
                "operations": [
                    {
                        "operation": "replace",
                        "path": "/status",
                        "value": "ERROR"
                    }
                ]
            }
        )
        response = self.fetch(
            '/api/v1/requests/' + str(self.request.id),
            method='PATCH',
            body=body,
            headers={'content-type': 'application/json'},
        )
        self.assertEqual(response.code, 200)
