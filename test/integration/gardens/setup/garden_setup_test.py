import pytest
from brewtils.schema_parser import SchemaParser


@pytest.mark.usefixtures('easy_client', 'parser')
class TestGardenSetup(object):

    def test_system_register_successful(self):

        gardens = self.parser.parse_garden(self.easy_client.client.session.get("api/v1/gardens/"))

        assert len(gardens) == 1
