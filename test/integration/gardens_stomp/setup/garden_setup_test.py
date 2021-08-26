import time
from typing import List

import pytest
from brewtils.models import Garden, PatchOperation

try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request
except (ImportError, ValueError):
    from ...helper import wait_for_response
    from ...helper.assertion import assert_successful_request


class IntegrationTestSetupFailure(Exception):
    pass


@pytest.fixture(scope="class")
def system_spec():
    return {
        "namespace": "childdocker",
        "system": "echo",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "say",
    }


@pytest.mark.usefixtures(
    "easy_client", "parser", "child_easy_client", "request_generator"
)
class TestGardenSetup(object):
    parent_garden_name = "default"
    child_garden_name = "childdocker"

    def _get_gardens(self) -> List[Garden]:
        """Return a list of the gardens present on beer garden."""
        gardens = self.parser.parse_garden(
            self.easy_client.client.session.get(
                self.easy_client.client.base_url + "api/v1/gardens/"
            ).json(),
            many=True,
        )

        if len(gardens) > 0:
            return gardens

        raise IntegrationTestSetupFailure("No Gardens found")

    def _get_child_garden(self) -> Garden:
        """Return the garden whose name indicates its a child garden."""
        child = list(
            filter(lambda x: x.name == self.child_garden_name, self._get_gardens())
        )

        if len(child) == 0:
            raise IntegrationTestSetupFailure("No child Garden found")
        elif len(child) > 1:
            # this normally shouldn't happen in this test environment
            raise IntegrationTestSetupFailure("Multiple child Gardens found")

        return child.pop()

    def _prepare_beer_garden(self) -> None:
        """Ensure the beer garden environment is correct for the tests."""
        parent, child, other = [], [], []
        gardens = self._get_gardens()

        # partition the gardens on the system
        for garden in gardens:
            if garden.name == self.parent_garden_name:
                parent.append(garden)
            elif garden.name == self.child_garden_name:
                child.append(garden)
            else:
                other.append(garden)

        # if not len(parent) > 0:
        #     raise IntegrationTestSetupFailure("Empty parent list")
        # _ = parent.pop(0)

        for garden_list, garden_name, the_client, label in [
            (parent, self.parent_garden_name, self.easy_client, "parent"),
            (child, self.child_garden_name, self.child_easy_client, "child")
        ]:
            if len(garden_list) == 0:
                # if there is no garden of this type, create one
                if not the_client.client.session.post(
                    the_client.client.base_url + "api/v1/gardens",
                    data=self.parser.serialize_garden(Garden(name=garden_name)),
                    headers=the_client.client.JSON_HEADERS,
                ).ok:
                    raise IntegrationTestSetupFailure(
                        f"No {label} garden present and unable to create one"
                    )
            else:
                _ = garden_list.pop()

        # if len(child) == 0:
        #     # if there is no child garden, create one
        #     if not self.easy_client.client.session.post(
        #         self.easy_client.client.base_url + "api/v1/gardens",
        #         data=self.parser.serialize_garden(Garden(name=self.child_garden_name)),
        #         headers=self.easy_client.client.JSON_HEADERS,
        #     ).ok:
        #         raise IntegrationTestSetupFailure(
        #             "No child garden present and unable to create one"
        #         )
        #
        # else:
        #     _ = child.pop(0)

        # so we can be 100% sure that there are exactly 2 gardens (parent and child),
        # delete any other gardens if they exist
        for garden in parent + child + other:
            self.easy_client.client.session.delete(
                self.easy_client.client.base_url + "api/v1/gardens/" + garden.name
            )

    def setup_method(self, _) -> None:
        """Use one of the `pytest`-preferred ways to initialize state before a test."""
        self._prepare_beer_garden()

    def test_update_garden_connection_info(self):
        child_garden_dict = self.parser.serialize_garden(
            self._get_child_garden(), to_string=False
        )

        child_garden_dict["connection_type"] = "STOMP"
        child_garden_dict["connection_params"] = {
            "stomp": {
                "host": "activemq",
                "port": 61613,
                "send_destination": "Beer_Garden_Operations_Parent",
                "subscribe_destination": "Beer_Garden_Events_Parent",
                "username": "beer_garden",
                "password": "password",
                "ssl": {"use_ssl": False},
            }
        }

        patch = PatchOperation(operation="config", path="", value=child_garden_dict)
        payload = self.parser.serialize_patch(patch)
        updated_response = self.easy_client.client.session.patch(
            self.easy_client.client.base_url
            + "api/v1/gardens/"
            + self.child_garden_name,
            data=payload,
            headers=self.easy_client.client.JSON_HEADERS,
        )

        assert updated_response.ok

    def test_garden_manual_register_successful(self):

        response = self.easy_client.client.session.get(
            self.easy_client.client.base_url + "api/v1/gardens/"
        )

        gardens = self.parser.parse_garden(response.json(), many=True)

        assert len(gardens) == 2

    def test_run_sync(self):
        # Give BG a second to setup connection
        time.sleep(5)
        patch = PatchOperation(operation="sync", path="")

        payload = self.parser.serialize_patch(patch)

        response = self.easy_client.client.session.patch(
            self.easy_client.client.base_url
            + "api/v1/gardens/"
            + self.child_garden_name,
            data=payload,
            headers=self.easy_client.client.JSON_HEADERS,
        )

        assert response.ok

        # Give BG a sync
        time.sleep(5)  # TODO: verify if these sleeps are actually needed

    def test_child_systems_register_successful(self):
        systems = self.child_easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        print(namespaces)
        assert (
            self.child_garden_name in namespaces.keys()
            and namespaces[self.child_garden_name] > 0
        )

    def test_child_request_from_parent(self):
        request = self.request_generator.generate_request(
            parameters={"message": "test_string", "loud": True}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="test_string!!!!!!!!!")

    def test_child_request_from_child(self):
        request = self.request_generator.generate_request(
            parameters={"message": "test_string", "loud": True}
        )
        response = wait_for_response(self.child_easy_client, request)
        assert_successful_request(response, output="test_string!!!!!!!!!")

    def test_verify_requests(self):
        requests = self.easy_client.find_requests()

        assert len(requests) == 2

    # TODO Add wait test
