import pytest
from brewtils.models import PatchOperation
import time

try:
    from helper.assertion import assert_successful_request
    from helper import wait_for_response, delete_plugins
    from helper.plugin import create_plugin, start_plugin, stop_plugin, TestPluginV1
except:
    from ...helper.assertion import assert_successful_request
    from ...helper import wait_for_response, delete_plugins
    from ...helper.plugin import (create_plugin, start_plugin, stop_plugin,
                                  TestPluginV1)


@pytest.fixture(scope="class")
def system_spec():
    return {'namespace': 'childdocker', 'system': 'test', 'system_version': '3.0.0.dev0', 'instance_name': 'default',
            'command': 'add'}


@pytest.mark.usefixtures('easy_client', 'parser', 'child_easy_client', 'request_generator')
class TestGardenSetup(object):
    child_garden_name = "childdocker"

    @pytest.fixture(autouse=True)
    def manage_plugin(self):
        """Ensure there are no "test" plugins before or after the test"""

        plugin = create_plugin("test", "3.0.0.dev0", TestPluginV1)
        start_plugin(plugin, self.child_easy_client)
        # Give child a couple seconds to publish events
        time.sleep(15)
        yield
        stop_plugin(plugin)
        delete_plugins(self.child_easy_client, "test")

    def test_garden_auto_register_successful(self):

        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")

        gardens = self.parser.parse_garden(response.json(), many=True)

        print(gardens)
        assert len(gardens) == 2

    def test_update_garden_connection_info(self):

        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")
        gardens = self.parser.parse_garden(response.json(), many=True)

        child_garden = None;
        for garden in gardens:
            if garden.name == self.child_garden_name:
                child_garden = garden
                break

        child_garden.connection_type = "HTTP"
        child_garden.connection_params = {"host": "beer-garden-child", "port": 2337, "ssl": False}

        patch = PatchOperation(operation="config", path='',
                               value=self.parser.serialize_garden(child_garden, to_string=False))

        payload = self.parser.serialize_patch(patch)

        print(payload)
        response = self.easy_client.client.session.patch(
            self.easy_client.client.base_url + "api/v1/gardens/" + self.child_garden_name, data=payload,
            headers=self.easy_client.client.JSON_HEADERS
        )

        assert response.ok

    def test_child_systems_register_successful(self):

        systems = self.child_easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        print(namespaces)
        assert self.child_garden_name in namespaces.keys() and namespaces[self.child_garden_name] > 0

    def test_child_systems_register_successful(self):

        systems = self.easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        print(namespaces)
        assert self.child_garden_name in namespaces.keys() and namespaces[self.child_garden_name] > 0

    def test_child_request_from_parent(self):
        request = self.request_generator.generate_request(parameters={"a": 1, "b": 2})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="3")

    def test_child_request_from_child(self):
        request = self.request_generator.generate_request(parameters={"a": 1, "b": 2})
        response = wait_for_response(self.child_easy_client, request)
        assert_successful_request(response, output="3")

    def test_verify_requests(self):
        requests = self.easy_client.find_requests()

        assert len(requests) == 2
