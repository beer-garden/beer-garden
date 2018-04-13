import pytest
import time

from helper import RequestGenerator, setup_easy_client, wait_for_in_progress, COMPLETED_STATUSES


@pytest.fixture(scope="class")
def system_spec():
    return {'system': 'concurrent-sleeper', 'system_version': '1.0.0.dev0',
            'instance_name': 'default', 'command': 'sleep'}


@pytest.mark.usefixtures('easy_client', 'request_generator')
class TestConcurrentSleeper(object):

    def test_process_multiple_request(self):
        """A plugin with max_concurrent > 1 can process more than one request at a time."""

        # The amount here means that it is impossible for this test to complete in less than 2 seconds.
        amounts = [2, 1]
        first_request_dict = self.request_generator.generate_request(parameters={"amount": amounts[0]})
        second_request_dict = self.request_generator.generate_request(parameters={"amount": amounts[1]})

        # Generate the first request and wait for it to be marked as "IN_PROGRESS"
        first_request = wait_for_in_progress(self.easy_client, first_request_dict, timeout=0.5)

        # Generate a second request and wait for it to be marked as "IN_PROGRESS"
        second_request = wait_for_in_progress(self.easy_client, second_request_dict, timeout=0.5)

        # Now that the second request is in progress, the first one should still be in progress
        first_request = self.easy_client.find_unique_request(id=first_request.id)
        assert first_request.status == "IN_PROGRESS"

        # Now we go through and wait for both requests to be finished.
        completed = False
        time_waited = 0
        total_timeout = sum(amounts) + 1
        while not completed:
            first_request = self.easy_client.find_unique_request(id=first_request.id)
            second_request = self.easy_client.find_unique_request(id=second_request.id)

            completed = (first_request.status in COMPLETED_STATUSES and second_request.status in COMPLETED_STATUSES)

            time.sleep(0.1)
            time_waited += 0.1
            if time_waited > total_timeout:
                raise ValueError("Waited too long for the requests to complete.")
