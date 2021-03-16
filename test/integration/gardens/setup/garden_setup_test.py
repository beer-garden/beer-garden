import pytest
from brewtils.schema_parser import SchemaParser
from helper.assertion import assert_system_running

@pytest.mark.usefixtures('easy_client', 'parser', 'child_easy_client')
class TestGardenSetup(object):

    def test_garden_auto_register_successful(self):

        #parser = SchemaParser()
        response = self.easy_client.client.session.get(self.easy_client.client.base_url + "api/v1/gardens/")

        gardens = self.parser.parse_garden(response.json(), many=True)

        print(gardens)
        assert len(gardens) == 2

    def test_child_systems_register_successful(self):

        systems = self.child_easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        print(namespaces)
        assert namespaces["child-docker"] > 0

    def test_child_systems_register_successful(self):

        systems = self.easy_client.find_systems()

        namespaces = dict()

        for system in systems:
            if system.namespace not in namespaces.keys():
                namespaces[system.namespace] = 1
            else:
                namespaces[system.namespace] += 1

        print(namespaces)
        assert namespaces["child-docker"] > 0

