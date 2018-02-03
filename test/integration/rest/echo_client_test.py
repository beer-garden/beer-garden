import unittest

from helper import setup_easy_client, RequestGenerator, wait_for_response
from helper.assertions import *


class EchoClientTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "echo"
        self.system_version = "1.0.0.dev"
        self.instance_name = "default"
        self.command = "say"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  command=self.command,
                                                  instance_name=self.instance_name)

    def test_say_custom_string_and_loud(self):
        request = self.request_generator.generate_request(parameters={"message": "test_string", "loud": True})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="test_string!!!!!!!!!")

    def test_say_no_parameters_provided(self):
        request = self.request_generator.generate_request()
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="Hello, World!")

    def test_non_nullable_string_set_to_null(self):
        request = self.request_generator.generate_request(parameters={"message": None, "loud": False})
        assert_validation_error(self, self.easy_client, request)

    def test_non_nullable_bool_set_to_null(self):
        request = self.request_generator.generate_request(parameters={"message": "test_string", "loud": None})
        assert_validation_error(self, self.easy_client, request)


if __name__ == '__main__':
    unittest.main()
