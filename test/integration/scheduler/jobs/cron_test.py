import pytest
from brewtils import get_easy_client
from brewtils.models import CronTrigger, RequestTemplate, Job
import time, datetime

try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request, assert_validation_error
except:
    from ...helper import wait_for_response
    from ...helper.assertion import assert_successful_request, assert_validation_error


@pytest.fixture()
def system_spec():
    return {'system': 'echo', 'system_version': '3.0.0.dev0', 'instance_name': 'default',
            'command': 'say', 'parameters': {'message': "hello", 'loud': False}}


@pytest.mark.usefixtures('easy_client')
class TestCron(object):

    def test_start_date_job(self, system_spec):
        # self.easy_client = get_easy_client(**{"bg_host": "localhost",
        #                                       "bg_port": 2337,
        #                                       "ssl_enabled": False})

        job_name = "test_start_date_job"
        delay_start = 60 * 2
        job_wait = 5

        start_date = int(round((time.time() + delay_start) * 1000))

        template = RequestTemplate(
            system=system_spec['system'],
            system_version=system_spec['system_version'],
            instance_name=system_spec['instance_name'],
            command=system_spec['command'],
            parameters=system_spec['parameters'],
            comment=job_name + ' Job',
            output_type="STRING"

        )

        trigger = CronTrigger(year="*",
                              month="*",
                              day="*",
                              week="*",
                              day_of_week="*",
                              hour="*",
                              minute="*",
                              second=f"*/{job_wait}",
                              start_date=start_date,
                              end_date=None,
                              jitter=None,
                              timezone="UTC")
        trigger.reschedule_on_finish = True

        job = Job(
            name=job_name,
            trigger_type='cron',
            trigger=trigger,
            request_template=template,
            status="RUNNING",
            coalesce=True,
            max_instances=1
        )

        job_response = self.easy_client.create_job(job)
        assert job_response is not None

        # Verify it hasn't ran yet
        time.sleep(job_wait + 5)
        found_jobs = self.easy_client.find_jobs(name=job_name)
        if time.time() < start_date:
            assert found_jobs[0].success_count == 0
        else:
            assert False

        # Verify that is can run
        time.sleep(delay_start + job_wait)
        found_jobs = self.easy_client.find_jobs(name=job_name)

        assert len(found_jobs) == 1
        assert found_jobs[0] is not None
        assert found_jobs[0].success_count > 0

        # Verify that the job doesn't get deleted
        time.sleep(job_wait)

        found_jobs = self.easy_client.find_jobs(name=job_name)

        assert len(found_jobs) == 1
        assert found_jobs[0] is not None
        assert found_jobs[0].success_count > 1
        assert self.easy_client.remove_job(found_jobs[0].id)
