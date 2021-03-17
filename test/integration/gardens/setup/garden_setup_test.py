import time

import pytest
from brewtils.schema_parser import SchemaParser
from brewtils.models import Garden, PatchOperation
from helper.assertion import assert_system_running


@pytest.mark.usefixtures('easy_client', 'parser', 'child_easy_client')
class TestGardenSetup(object):

    child_garden_name = "childdocker"

    def test_garden_auto_register_successful(self):

        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")

        gardens = self.parser.parse_garden(response.json(), many=True)

        print(gardens)
        assert len(gardens) == 2

    # def test_garden_register(self):
    #
    #     child_garden = Garden(name="child-docker", connection_type="HTTP",
    #                           connection_params={"host": "beer-garden-child", "port": 2347, "ssl": False})
    #
    #     payload = self.parser.serialize_garden(child_garden)
    #     response = self.easy_client.client.session.post(
    #         self.easy_client.client.base_url + "api/v1/gardens/", data=payload, headers=self.easy_client.client.JSON_HEADERS
    #     )
    #
    #     assert response.ok
    #
    #     response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")
    #
    #     gardens = self.parser.parse_garden(response.json(), many=True)
    #
    #     print(gardens)
    #     assert len(gardens) == 2

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

        patch = PatchOperation(operation="config", path='', value=self.parser.serialize_garden(child_garden))

        payload = self.parser.serialize_patch(patch)
        response = self.easy_client.client.session.patch(
            self.easy_client.client.base_url + "api/v1/gardens/" + self.child_garden_name, data=payload,
            headers=self.easy_client.client.JSON_HEADERS
        )

        assert response.status == 200

    # def test_force_sync(self):
    #
    #     patch = PatchOperation(operation="sync", path='', value=None)
    #     payload = self.parser.serialize_patch(patch)
    #
    #     response = self.easy_client.client.session.patch(
    #         self.easy_client.client.base_url + "api/v1/gardens/"+self.child_garden_name, data=payload,
    #         headers=self.easy_client.client.JSON_HEADERS
    #     )
    #
    #     assert response.ok
    #
    #     # Wait for the child to sync before proceeding
    #     time.sleep(30)

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
