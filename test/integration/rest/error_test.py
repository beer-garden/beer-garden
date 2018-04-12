import unittest
import json

from helper import RequestGenerator, setup_easy_client, wait_for_response
from helper.assertions import *


class ErrorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "error"
        self.command = "string_error_message"
        self.system_version = "1.0.0.dev0"
        self.instance_name = "default"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  command=self.command,
                                                  instance_name=self.instance_name)

    def test_error_on_request(self):
        request = self.request_generator.generate_request()
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)

    def test_format_output_on_json_request(self):
        request = self.request_generator.generate_request(command="error_string_output_type_json")
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)
        self.assertDictEqual({"message": "This is a string", "attributes": {}}, json.loads(response.output))


if __name__ == '__main__':
    unittest.main()
