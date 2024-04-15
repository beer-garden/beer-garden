import pytest
from brewtils.models import PatchOperation
from brewtils.schema_parser import SchemaParser

try:
    from helper import wait_for_response
    from helper.assertion import assert_errored_request, assert_successful_request
except (ImportError, ValueError):
    from ...helper import wait_for_response
    from ...helper.assertion import assert_errored_request, assert_successful_request


@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "echo-sleeper",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
    }


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestEchoSleeper(object):

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

    def test_parent_with_children_success(self):
        request = self.request_generator.generate_request(
            command="say_sleep", parameters={"message": "foo", "amount": 0.01}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        assert len(response.children) == 2
        for child_request in response.children:
            assert_successful_request(child_request)

    def test_parent_with_error_does_not_raise(self):
        request = self.request_generator.generate_request(
            command="say_error_and_catch", parameters={"message": "foo"}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        assert len(response.children) == 2
        for child_request in response.children:
            if child_request.system == "echo":
                assert_successful_request(child_request)
            elif child_request.system == "error":
                assert_errored_request(child_request)

    def test_parent_with_error_and_raise(self):
        request = self.request_generator.generate_request(
            command="say_error_and_raise", parameters={"message": "foo"}
        )
        response = wait_for_response(self.easy_client, request)
        assert_errored_request(response)
        assert len(response.children) == 2
        for child_request in response.children:
            if child_request.system == "echo":
                assert_successful_request(child_request)
            elif child_request.system == "error":
                assert_errored_request(child_request)
