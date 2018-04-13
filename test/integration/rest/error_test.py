import json
import pytest

from helper import RequestGenerator, setup_easy_client, wait_for_response
from helper.assertion import assert_errored_request

@pytest.fixture(scope="class")
def system_spec():
    return {'system': 'error', 'system_version': '1.0.0.dev0', 'instance_name': 'default',
            'command': 'string_error_message'}


@pytest.mark.usefixtures('easy_client', 'request_generator')
class TestError(object):

    def test_error_on_request(self):
        request = self.request_generator.generate_request()
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)

    def test_format_output_on_json_request(self):
        request = self.request_generator.generate_request(command="error_string_output_type_json")
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)
        assert {"message": "This is a string", "attributes": {}} == json.loads(response.output)
