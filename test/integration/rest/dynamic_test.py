import unittest

from helper import setup_easy_client, RequestGenerator, wait_for_response
from helper.assertions import *


class DynamicTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "dynamic"
        self.system_version = "1.0.0.dev"
        self.instance_name = "default"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  instance_name=self.instance_name)

    def test_say_specific_in_choice(self):
        request = self.request_generator.generate_request(command="say_specific", parameters={"message": "a"})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="a")

    def test_say_specific_not_in_choice(self):
        request = self.request_generator.generate_request(command="say_specific",
                                                          parameters={"message": "NOT_IN_CHOICES"})
        assert_validation_error(self, self.easy_client, request, regex='not a valid choice')

    def test_say_specific_from_command_in_choice(self):
        request = self.request_generator.generate_request(command="say_specific_from_command", parameters={"message": "a"})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="a")

    def test_say_specific_from_command_not_in_choice(self):
        request = self.request_generator.generate_request(command="say_specific_from_command",
                                                          parameters={"message": "NOT_IN_CHOICES"})
        assert_validation_error(self, self.easy_client, request, regex='not a valid choice')

    def test_say_specific_from_command_nullable_message(self):
        request = self.request_generator.generate_request(command="say_specific_from_command_nullable",
                                                          parameters={"message": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_say_specific_from_command_nullable_not_in_choice(self):
        request = self.request_generator.generate_request(command="say_specific_from_command_nullable",
                                                          parameters={"message": "NOT_IN_CHOICES"})
        assert_validation_error(self, self.easy_client, request, regex='not a valid choice')

    def test_say_specific_from_url_good_choice(self):
        request = self.request_generator.generate_request(command="say_specific_from_url",
                                                          parameters={"message": "Kentucky"})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="Kentucky")

    def test_say_specific_from_url_bad_choice(self):
        request = self.request_generator.generate_request(command="say_specific_from_url",
                                                          parameters={"message": "NOT_IN_CHOICES"})
        assert_validation_error(self, self.easy_client, request, regex='not a valid choice')

    def test_say_specific_from_url_nullable(self):
        request = self.request_generator.generate_request(command="say_specific_from_url_nullable",
                                                          parameters={"message": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_say_specific_non_strict_out_of_choice(self):
        request = self.request_generator.generate_request(command="say_specific_non_strict_typeahead",
                                                          parameters={"message": "NOT_IN_CHOICE"})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="NOT_IN_CHOICE")


if __name__ == '__main__':
    unittest.main()
