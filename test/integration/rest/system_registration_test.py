import pytest
import unittest

from helper.plugin import *
from helper import setup_easy_client, delete_plugins
from helper.assertions import assert_system_running
from brewtils.errors import BrewmasterValidationError, BGConflictError


class SystemRegistrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()
        delete_plugins(cls.easy_client, "test")

    def tearDown(self):
        delete_plugins(self.easy_client, "test")

    def test_system_register_successful(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        stop_plugin(plugin)

    def test_system_register_update_data(self):
        # Register the first plugin first.
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        # We shut down this plugin so we can start a different one with updated descriptions
        stop_plugin(plugin)

        plugin = create_plugin("test", "1.0.0", TestPluginV1BetterDescriptions, description="A better description",
                               metadata={"foo": "bar"}, icon_name="fa-coffee", display_name="new_display_name")
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0",
                              system={"description": "A better description",
                                      "metadata": {"foo": "bar"}, "icon_name": "fa-coffee",
                                      'display_name': 'new_display_name'})
        stop_plugin(plugin)

    def test_system_register_dev_different_commands(self):
        plugin = create_plugin("test", "1.0.0.dev", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0.dev")
        # We shut down this plugin so we can start a different one with updated descriptions
        stop_plugin(plugin)

        plugin = create_plugin("test", "1.0.0.dev", TestPluginV2)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0.dev")
        stop_plugin(plugin)

    def test_system_register_different_commands_should_fail(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        stop_plugin(plugin)

        plugin = create_plugin("test", "1.0.0", TestPluginV2)
        with self.assertRaises(BrewmasterValidationError):
            self.easy_client.create_system(plugin.system)

    def test_system_register_different_versions(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")

        plugin = create_plugin("test", "2.0.0", TestPluginV2)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        assert_system_running(self.easy_client, "test", "2.0.0")

    def test_system_register_same_display_name(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1, display_name="TEST")
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")

        new_plugin = create_plugin("new_test", "1.0.0", TestPluginV1, display_name="TEST")
        with self.assertRaises(BGConflictError):
            self.easy_client.create_system(new_plugin.system)

    @pytest.mark.skip(reason="Depends on beer-garden/bartender#7")
    def test_system_register_same_instance_name(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")

        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        with self.assertRaises(BrewmasterValidationError):
            self.easy_client.create_system(plugin.system)


if __name__ == '__main__':
    unittest.main()
