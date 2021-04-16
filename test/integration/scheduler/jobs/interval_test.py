import pytest
from brewtils import get_easy_client
from brewtils.models import IntervalTrigger, RequestTemplate, Job
import time

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
class TestInterval(object):

    def test_no_namespace_job(self, system_spec):

        job_name = "test_no_namespace_job"
        job_wait = 30

        template = RequestTemplate(
            system=system_spec['system'],
            system_version=system_spec['system_version'],
            instance_name=system_spec['instance_name'],
            command=system_spec['command'],
            parameters=system_spec['parameters'],
            comment=job_name + ' Job'
        )

        trigger = IntervalTrigger(seconds=job_wait)
        trigger.reschedule_on_finish = True

        job = Job(
            name=job_name,
            trigger_type='interval',
            trigger=trigger,
            request_template=template,
            status="RUNNING",
            coalesce=True,
            max_instances=1
        )

        job_response = self.easy_client.create_job(job)

        assert job_response is not None

        # Wait before checking plus a little extra
        time.sleep(job_wait + 15)

        found_jobs = self.easy_client.find_jobs(name=job_name)

        assert len(found_jobs) == 1

        assert found_jobs[0] is not None

        assert found_jobs[0].success_count > 0

        assert self.easy_client.remove_job(found_jobs[0].id)
