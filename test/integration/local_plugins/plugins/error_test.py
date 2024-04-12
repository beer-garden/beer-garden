import json

import pytest
from brewtils.models import PatchOperation
from brewtils.schema_parser import SchemaParser

try:
    from ...helper import wait_for_response
    from ...helper.assertion import assert_errored_request
except (ImportError, ValueError):
    from helper import wait_for_response
    from helper.assertion import assert_errored_request


@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "error",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "string_error_message",
    }


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestError(object):

    def test_stop_start(self, system_spec):
        test_ran = False

        system = self.easy_client.find_unique_system(
            name=system_spec["system"], version=system_spec["system_version"]
        )
        for instance in system.instances:
            if instance.name == system_spec["instance_name"]:
                assert instance.status == "RUNNING"

                stopped_instance = self.easy_client.client.patch_instance(
                    instance.id,
                    SchemaParser.serialize_patch(PatchOperation(operation="stop")),
                )
                assert stopped_instance.ok

                start_instance = self.easy_client.client.patch_instance(
                    instance.id,
                    SchemaParser.serialize_patch(PatchOperation(operation="start")),
                )
                assert start_instance.ok

                test_ran = True

        assert test_ran

    def test_error_on_request(self):
        request = self.request_generator.generate_request()
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)

    def test_format_output_on_json_request(self):
        request = self.request_generator.generate_request(
            command="error_string_output_type_json"
        )
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)
        assert json.loads(response.output) == {
            "message": "This is a string",
            "arguments": ["This is a string"],
            "attributes": {},
        }
