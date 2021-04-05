import pytest
from brewtils.models import PatchOperation, Garden

try:
    from helper.assertion import assert_successful_request
    from helper import wait_for_response
except:
    from ...helper.assertion import assert_successful_request
    from ...helper import wait_for_response


@pytest.fixture(scope="class")
def system_spec():
    return {'namespace': 'childdocker', 'system': 'echo', 'system_version': '3.0.0.dev0', 'instance_name': 'default',
            'command': 'say'}


@pytest.mark.usefixtures('easy_client', 'parser', 'child_easy_client', 'request_generator')
class TestGardenSetup(object):
    child_garden_name = "childdocker"

    def test_update_garden_connection_info(self):

        child_garden = Garden(name=self.child_garden_name,
                              connection_type="STOMP",
                              connection_params={"stomp_host": "localhost",
                                                 "stomp_port": 61613,
                                                 "stomp_send_destination": "Beer_Garden_Forward_Parent",
                                                 "stomp_subscribe_destination": "Beer_Garden_Operations_Parent",
                                                 "stomp_username": "beer_garden",
                                                 "stomp_password": "password",
                                                 "stomp_ssl": {"use_ssl": False},
                                                 })

        payload = self.parser.serialize_garden(child_garden)

        response = self.easy_client.client.session.post(
            self.easy_client.client.base_url + "api/v1/gardens", data=payload,
            headers=self.easy_client.client.JSON_HEADERS
        )

        assert response.ok

    def test_garden_manual_register_successful(self):

        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")

        gardens = self.parser.parse_garden(response.json(), many=True)

        assert len(gardens) == 2

    def test_run_sync(self):
        patch = PatchOperation(operation="sync", path='')

        payload = self.parser.serialize_patch(patch)

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
        request = self.request_generator.generate_request(parameters={"message": "test_string", "loud": True})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="test_string!!!!!!!!!")

    def test_child_request_from_child(self):
        request = self.request_generator.generate_request(parameters={"message": "test_string", "loud": True})
        response = wait_for_response(self.child_easy_client, request)
        assert_successful_request(response, output="test_string!!!!!!!!!")

    def test_verify_requests(self):
        requests = self.easy_client.find_requests()

        assert len(requests) == 2

    # TODO Add wait test