import unittest
import time
from helper import RequestGenerator, setup_easy_client, wait_for_in_progress, COMPLETED_STATUSES


class ConcurrentSleeperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "concurrent-sleeper"
        self.command = "sleep"
        self.system_version = "1.0.0.dev0"
        self.instance_name = "default"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  command=self.command,
                                                  instance_name=self.instance_name)

    def test_process_multiple_request(self):
        """This tests ensures that a multi-threaded plugin can process and complete multiple-requests at once"""

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
        self.assertEqual(first_request.status, "IN_PROGRESS")

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


if __name__ == '__main__':
    unittest.main()
