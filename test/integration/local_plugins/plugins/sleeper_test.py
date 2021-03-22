import pytest
import time

try:
    from helper import wait_for_in_progress, COMPLETED_STATUSES
except:
    from ...helper import wait_for_in_progress, COMPLETED_STATUSES

@pytest.fixture(scope="class")
def system_spec():
    return {'system': 'sleeper', 'system_version': '3.0.0.dev0', 'instance_name': 'default',
            'command': 'sleep'}


@pytest.mark.usefixtures('easy_client', 'request_generator')
class TestSleeper(object):

    @pytest.mark.skip("Skipping until we set max current by default")
    def test_only_process_single_request_at_a_time(self):
        """A single-threaded plugin shouldn't process more than one request at a time."""

        # The amount here means that it is impossible for this test to complete in less than 2.1 seconds.
        amounts = [2, 0.1]
        first_request_dict = self.request_generator.generate_request(parameters={"amount": amounts[0]})
        second_request_dict = self.request_generator.generate_request(parameters={"amount": amounts[1]})

        # Generate the first request and wait for it to be marked as "IN_PROGRESS"
        first_request = wait_for_in_progress(self.easy_client, first_request_dict, timeout=0.5)

        # Generate a second request now that the first one is processing.
        second_request = self.easy_client.create_request(second_request_dict)

        # Now we go through and wait for both requests to be finished. We also check to make sure that
        # the second request didn't start unless the first one is in some form of a completed state.
        completed = False
        time_waited = 0
        total_timeout = sum(amounts) + 1
        while not completed:
            first_request = self.easy_client.find_unique_request(id=first_request.id)
            second_request = self.easy_client.find_unique_request(id=second_request.id)

            if second_request.status != 'CREATED':
                # We fetch the first_request again to make sure we didn't run into some kind of weird timing bug where
                # request 1 finished between the two fetches.
                first_request = self.easy_client.find_unique_request(id=first_request.id)
                assert first_request.status in COMPLETED_STATUSES, "Second request started in a single-threaded " \
                                                                   "plugin before the first one was completed."

            completed = (first_request.status in COMPLETED_STATUSES and second_request.status in COMPLETED_STATUSES)
            time.sleep(0.1)
            time_waited += 0.1
            if time_waited > total_timeout:
                raise ValueError("Waited too long for the requests to complete.")
