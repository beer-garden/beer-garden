import pytest
from helper import setup_system_client, wait_for_response, RequestGenerator, delete_plugins
from helper.plugin import (create_plugin, start_plugin, stop_plugin,
                           TestPluginV1, TestPluginV2,
                           TestPluginV1BetterDescriptions)

@pytest.mark.usefixtures('easy_client')
class TestRequestListApi(object):

    @pytest.fixture(autouse=True)
    def delete_test_plugin(self):
        """Ensure there are no "test" plugins before or after the test"""
        delete_plugins(self.easy_client, "test")
        yield
        delete_plugins(self.easy_client, "test")

    @staticmethod
    @pytest.fixture
    def echo_generator():
        return RequestGenerator(
            system='test',
            system_version='1.0.0',
            instance_name='default',
            command='add',
        )

    def _start_plugin(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        return plugin

    def test_get_requests(self, echo_generator):

        plugin = self._start_plugin()

        # Make a couple of requests just to ensure there are some
        request_1 = echo_generator.generate_request(
            parameters={"x": 1, "y": 2})
        request_2 = echo_generator.generate_request(
            parameters={"x": 1, "y": 2})
        wait_for_response(self.easy_client, request_1, timeout=30)
        wait_for_response(self.easy_client, request_2, timeout=30)

        response = self.easy_client.find_requests(length=2)
        assert len(response) == 2

        # Make sure we don't get an empty object (Brew-view 2.3.8)
        assert response[0].command is not None

        stop_plugin(plugin)
