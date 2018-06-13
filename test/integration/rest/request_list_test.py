import pytest

from helper import setup_easy_client, RequestGenerator, wait_for_response
from helper.assertion import assert_successful_request, assert_validation_error


@pytest.fixture(scope="class")
def system_spec():
    return {'system': 'echo', 'system_version': '1.0.0.dev0', 'instance_name': 'default',
            'command': 'say'}


@pytest.mark.usefixtures('easy_client', 'request_generator')
class TestRequestListApi(object):

    def test_get_requests(self):
        # Make a couple of requests just to ensure there are some
        request_1 = self.request_generator.generate_request(parameters={"message": "test_string", "loud": True})
        request_2 = self.request_generator.generate_request(parameters={"message": "test_string", "loud": False})
        response_1 = wait_for_response(self.easy_client, request_1)
        response_2 = wait_for_response(self.easy_client, request_2)

        response = self.easy_client.find_requests(length=2)
        assert len(response) == 2

        # Make sure we don't get an empty object (Brew-view 2.3.8)
        assert response[0].command is not None
