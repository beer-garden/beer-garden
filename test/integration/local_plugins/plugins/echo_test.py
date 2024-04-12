import pytest

try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request, assert_validation_error
except (ImportError, ValueError):
    from ...helper import wait_for_response
    from ...helper.assertion import assert_successful_request, assert_validation_error
from brewtils.schema_parser import SchemaParser
from brewtils.models import PatchOperation

@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "echo",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "say",
    }


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestEcho(object):

    def test_stop_start(self, system_spec):
        system = self.easy_client.find_unique_system(name=system_spec["system"], version=system_spec["system_version"])
        test_ran = False
        for instance in system.instances:
            if instance.name == system_spec["instance_name"]:
                assert instance.status == "RUNNING"
 
                stopped_instance = self.easy_client.client.patch_instance(instance.id, SchemaParser.serialize_patch(PatchOperation(operation="stop")))
                assert stopped_instance.ok

                assert stopped_instance.json()["status"] == "STOPPED"

                start_instance = self.easy_client.client.patch_instance(instance.id, SchemaParser.serialize_patch(PatchOperation(operation="start")))
                assert start_instance.ok
                assert start_instance.json()["status"] == "RUNNING"
                assert stopped_instance == start_instance
                
                test_ran = True
        
        assert test_ran

    def test_say_custom_string_and_loud(self):
        request = self.request_generator.generate_request(
            parameters={"message": "test_string", "loud": True}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="test_string!!!!!!!!!")

    def test_say_custom_string_unicode(self):
        request = self.request_generator.generate_request(
            parameters={"message": "\U0001F4A9"}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="\U0001F4A9")

    def test_say_no_parameters_provided(self):
        request = self.request_generator.generate_request()
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="Hello, World!")

    def test_non_nullable_string_set_to_null(self):
        request = self.request_generator.generate_request(
            parameters={"message": None, "loud": False}
        )
        assert_validation_error(self, self.easy_client, request)

    def test_non_nullable_bool_set_to_null(self):
        request = self.request_generator.generate_request(
            parameters={"message": "test_string", "loud": None}
        )
        assert_validation_error(self, self.easy_client, request)
