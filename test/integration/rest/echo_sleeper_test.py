import unittest

from helper import setup_easy_client, RequestGenerator, wait_for_response
from helper.assertions import *


class EchoSleeperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "echo-sleeper"
        self.system_version = "1.0.0.dev"
        self.instance_name = "default"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  instance_name=self.instance_name)

    def test_parent_with_children_success(self):
        request = self.request_generator.generate_request(command="say_sleep", parameters={"message": "foo",
                                                                                           "amount": 0.01})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertEqual(len(response.children), 2)
        for child_request in response.children:
            assert_successful_request(child_request)

    def test_parent_with_error_does_not_raise(self):
        request = self.request_generator.generate_request(command="say_error_and_catch", parameters={"message": "foo"})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertEqual(len(response.children), 2)
        for child_request in response.children:
            if child_request.system == "echo":
                assert_successful_request(child_request)
            elif child_request.system == "error":
                assert_errored_request(child_request)

    def test_parent_with_error_and_raise(self):
        request = self.request_generator.generate_request(command="say_error_and_raise", parameters={"message": "foo"})
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)
        self.assertEqual(len(response.children), 2)
        for child_request in response.children:
            if child_request.system == "echo":
                assert_successful_request(child_request)
            elif child_request.system == "error":
                assert_errored_request(child_request)

if __name__ == '__main__':
    unittest.main()
