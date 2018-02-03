import unittest
import time
from helper import RequestGenerator, setup_easy_client, wait_for_in_progress, COMPLETED_STATUSES


class SleeperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "sleeper"
        self.command = "sleep"
        self.system_version = "1.0.0.dev"
        self.instance_name = "default"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  command=self.command,
                                                  instance_name=self.instance_name)

    def test_only_process_single_request_at_a_time(self):
        """This tests ensures that a single-threaded plugin cannot process more than one request at a time."""

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


if __name__ == '__main__':
    unittest.main()
