import json

import pytest

try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request
except (ImportError, ValueError):
    from ...helper import wait_for_response
    from ...helper.assertion import assert_successful_request


@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "AutoBrewClient",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
    }


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestAutobrew(object):
    def test_any_kwargs_success(self):
        parameters = {"foo": {"foo": ["a", "b", "c"], "bar": "baz"}, "bar": "baz"}
        request = self.request_generator.generate_request(
            command="any_kwargs", parameters=parameters
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        assert json.loads(response.output) == parameters
