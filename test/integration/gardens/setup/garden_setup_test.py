import pytest
from brewtils.schema_parser import SchemaParser
from helper.assertion import assert_system_running

@pytest.mark.usefixtures('easy_client', 'parser')
class TestGardenSetup(object):

    def test_garden_register_successful(self):

        #parser = SchemaParser()
        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")

        gardens = self.parser.parse_garden(response.json(), many=True)

        assert len(gardens) == 1

    def test_child_systems_register_successful(self):

        assert_system_running(self.easy_client, "echo", "3.0.0", garden="child")
