import pytest

from ...helper import wait_for_response
from ...helper.assertion import assert_successful_request, assert_errored_request


@pytest.fixture(scope="class")
def system_spec():
    return {'system': 'echo-sleeper', 'system_version': '3.0.0.dev0', 'instance_name': 'default'}


@pytest.mark.usefixtures('easy_client', 'request_generator')
class TestEchoSleeper(object):

    def test_parent_with_children_success(self):
        request = self.request_generator.generate_request(command="say_sleep", parameters={"message": "foo",
                                                                                           "amount": 0.01})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        assert len(response.children) == 2
        for child_request in response.children:
            assert_successful_request(child_request)

    def test_parent_with_error_does_not_raise(self):
        request = self.request_generator.generate_request(command="say_error_and_catch", parameters={"message": "foo"})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        assert len(response.children) == 2
        for child_request in response.children:
            if child_request.system == "echo":
                assert_successful_request(child_request)
            elif child_request.system == "error":
                assert_errored_request(child_request)

    def test_parent_with_error_and_raise(self):
        request = self.request_generator.generate_request(command="say_error_and_raise", parameters={"message": "foo"})
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)
        assert len(response.children) == 2
        for child_request in response.children:
            if child_request.system == "echo":
                assert_successful_request(child_request)
            elif child_request.system == "error":
                assert_errored_request(child_request)
