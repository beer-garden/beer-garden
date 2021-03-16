import pytest
from brewtils.schema_parser import SchemaParser


@pytest.mark.usefixtures('easy_client', 'parser')
class TestGardenSetup(object):

    def test_system_register_successful(self):

        parser = SchemaParser()
        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")

        gardens = parser.parse_garden(response.json(), many=True)

        assert len(gardens) == 1
