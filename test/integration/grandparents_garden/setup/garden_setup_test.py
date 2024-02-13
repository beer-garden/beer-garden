import pytest
import json
import time

# from time import sleep
# from brewtils.models import PatchOperation
#
# try:
#    from helper import wait_for_response
#    from helper.assertion import assert_successful_request
# except (ImportError, ValueError):
#    from ...helper import wait_for_response
#    from ...helper.assertion import assert_successful_request


@pytest.fixture(scope="class")
def system_spec():
    return {
        "namespace": "child",
        "system": "echo",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "say",
    }


@pytest.mark.usefixtures(
    "parser",
    "child_easy_client",
    "parent_easy_client",
    "grand_parent_easy_client",
    "request_generator",
)
class TestGardenSetup(object):
    child_garden_name = "child"

    def sync_parent(self):
        patches = json.dumps(
            [
                {
                    "operation": "sync",
                    "path": "",
                    "value": "",
                }
            ]
        )
        self.grand_parent_easy_client.client.patch_garden("parent", patches)
        time.sleep(5)

    def sync_child(self):
        patches = json.dumps(
            [
                {
                    "operation": "sync",
                    "path": "",
                    "value": "",
                }
            ]
        )
        self.parent_easy_client.client.patch_garden("child", patches)
        time.sleep(5)

    # def test_garden_auto_register_successful(self):
    #     response = self.grand_parent_easy_client.client.session.get(
    #         self.grand_parent_easy_client.client.base_url + "api/v1/gardens/"
    #     )

    #     gardens = self.parser.parse_garden(response.json(), many=True)

    #     print(gardens)
    #     assert len(gardens) == 2

    #     for garden in gardens:
    #         if garden.name == 'parent':
    #             assert len(garden.children) == 1

    def test_grandparent_counter(self):
        self.sync_parent()
        response = self.grand_parent_easy_client.client.session.get(
            self.grand_parent_easy_client.client.base_url + "api/v1/gardens/"
        )

        gardens = self.parser.parse_garden(response.json(), many=True)

        assert len(gardens) == 2

        for garden in gardens:
            if garden.name == "parent":
                for connection in garden.publishing_connections:
                    if connection.api == "HTTP":
                        assert connection.status == "PUBLISHING"
                    else:
                        assert connection.status == "NOT_CONFIGURED"
                assert len(garden.receiving_connections) == 1
                assert garden.receiving_connections[0].status == "RECEIVING"
                assert len(garden.children) == 1
                assert garden.children[0].name == "child"

            elif garden.name == "grandparent":
                assert len(garden.children) == 1
            else:
                assert False

    def test_parent_counter(self):
        self.sync_child()
        response = self.parent_easy_client.client.session.get(
            self.parent_easy_client.client.base_url + "api/v1/gardens/"
        )

        gardens = self.parser.parse_garden(response.json(), many=True)

        assert len(gardens) == 2

        for garden in gardens:
            if garden.name == "child":
                for connection in garden.publishing_connections:
                    if connection.api == "HTTP":
                        assert connection.status == "PUBLISHING"
                    else:
                        assert connection.status == "NOT_CONFIGURED"

                # Older gardens will not have receiving connections present
                if len(garden.receiving_connections) > 0:
                    assert len(garden.receiving_connections) == 1
                    assert garden.receiving_connections[0].status == "RECEIVING"
                    assert len(garden.children) == 0

            elif garden.name == "parent":
                assert len(garden.children) == 1
            else:
                assert False

    def test_child_counter(self):
        response = self.child_easy_client.client.session.get(
            self.child_easy_client.client.base_url + "api/v1/gardens/"
        )

        gardens = self.parser.parse_garden(response.json(), many=True)

        print(gardens)
        assert len(gardens) == 1

        for garden in gardens:
            assert garden.name in ["child"]

    def test_grandchildren(self):
        response = self.grand_parent_easy_client.client.session.get(
            self.grand_parent_easy_client.client.base_url + "api/v1/gardens/"
        )

        gardens = self.parser.parse_garden(response.json(), many=True)

        for garden in gardens:
            print(garden)
            assert not garden.has_parent

        for garden in gardens:
            if garden.name == "parent":
                assert garden.children is not None
                assert len(garden.children) == 1

        assert len(gardens) == 2

    def test_parent_systems_register_successful(self):
        systems = self.grand_parent_easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        assert len(namespaces) == 3
        assert namespaces["grandparent"] > 0
        assert namespaces["parent"] > 0
        assert namespaces["child"] > 0

    def test_child_systems_register_successful(self):
        systems = self.parent_easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        assert len(namespaces) == 2
        assert namespaces["parent"] > 0
        assert namespaces["child"] > 0

    # def test_update_garden_connection_info(self):
    #     response = self.easy_client.client.session.get(
    #         self.easy_client.client.base_url + "api/v1/gardens/"
    #     )
    #     gardens = self.parser.parse_garden(response.json(), many=True)

    #     child_garden = None
    #     for garden in gardens:
    #         if garden.name == self.child_garden_name:
    #             child_garden = garden
    #             break

    #     child_garden.connection_type = "HTTP"
    #     child_garden.connection_params = {
    #         "http": {"host": "beer-garden-child", "port": 2337, "ssl": False}
    #     }

    #     patch = PatchOperation(
    #         operation="config",
    #         path="",
    #         value=self.parser.serialize_garden(child_garden, to_string=False),
    #     )

    #     payload = self.parser.serialize_patch(patch)

    #     print(payload)
    #     response = self.easy_client.client.session.patch(
    #         self.easy_client.client.base_url
    #         + "api/v1/gardens/"
    #         + self.child_garden_name,
    #         data=payload,
    #         headers=self.easy_client.client.JSON_HEADERS,
    #     )

    #     assert response.ok

    # def test_child_systems_register_successful(self):
    #     systems = self.easy_client.find_systems()

    #     namespaces = dict()

    #     for system in systems:
    #         if system.namespace not in namespaces.keys():
    #             namespaces[system.namespace] = 1
    #         else:
    #             namespaces[system.namespace] += 1

    #     print(namespaces)
    #     assert (
    #         self.child_garden_name in namespaces.keys()
    #         and namespaces[self.child_garden_name] > 0
    #     )

    # def test_child_request_from_parent(self):
    #     request = self.request_generator.generate_request(
    #         parameters={"message": "test_string", "loud": True}
    #     )
    #     response = wait_for_response(self.easy_client, request)
    #     assert_successful_request(response, output="test_string!!!!!!!!!")

    # def test_child_request_from_child(self):
    #     request = self.request_generator.generate_request(
    #         parameters={"message": "test_string", "loud": True}
    #     )
    #     response = wait_for_response(self.child_easy_client, request)
    #     assert_successful_request(response, output="test_string!!!!!!!!!")

    # def test_verify_requests(self):
    #     sleep(0.5)  # TODO: it is ridiculous that this is necessary
    #     orig_requests_len = len(self.easy_client.find_requests())

    #     new_request_clients = [self.easy_client, self.child_easy_client]

    #     for client in new_request_clients:
    #         new_request = wait_for_response(
    #             client,
    #             self.request_generator.generate_request(
    #                 parameters={"message": "test_string", "loud": True}
    #             ),
    #         )
    #         assert new_request.status == "SUCCESS"

    #     new_requests_len = len(self.easy_client.find_requests())

    #     assert new_requests_len == orig_requests_len + len(new_request_clients)

    # TODO Add wait test
