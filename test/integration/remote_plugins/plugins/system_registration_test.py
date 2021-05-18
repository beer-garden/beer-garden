import pytest

from brewtils.errors import ValidationError

try:
    from helper import delete_plugins
    from helper.assertion import assert_system_running
    from helper.plugin import (
        create_plugin,
        start_plugin,
        stop_plugin,
        TestPluginV1,
        TestPluginV2,
        TestPluginV1BetterDescriptions,
    )
except:
    from ...helper import delete_plugins
    from ...helper.assertion import assert_system_running
    from ...helper.plugin import (
        create_plugin,
        start_plugin,
        stop_plugin,
        TestPluginV1,
        TestPluginV2,
        TestPluginV1BetterDescriptions,
    )


@pytest.mark.usefixtures("easy_client")
class TestSystemRegistration(object):
    @pytest.fixture(autouse=True)
    def delete_test_plugin(self):
        """Ensure there are no "test" plugins before or after the test"""
        delete_plugins(self.easy_client, "test")
        yield
        delete_plugins(self.easy_client, "test")

    def test_system_register_successful(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        stop_plugin(plugin)

    def test_system_register_update_data(self):
        # Register the standard plugin, then stop it
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        stop_plugin(plugin)

        # Now create the new plugin and register that one
        plugin = create_plugin(
            "test",
            "1.0.0",
            TestPluginV1BetterDescriptions,
            description="A better description",
            metadata={"foo": "bar"},
            icon_name="fa-coffee",
            display_name="new_display_name",
        )
        start_plugin(plugin, self.easy_client)
        assert_system_running(
            self.easy_client,
            "test",
            "1.0.0",
            system={
                "description": "A better description",
                "metadata": {"foo": "bar"},
                "icon_name": "fa-coffee",
                "display_name": "new_display_name",
            },
        )
        stop_plugin(plugin)

    def test_system_register_dev_different_commands(self):
        # Register the standard plugin, then stop it
        plugin = create_plugin("test", "1.0.0.dev", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0.dev")
        stop_plugin(plugin)

        # Now create the new plugin and register that one
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
        with pytest.raises(ValidationError):
            self.easy_client.create_system(plugin.system)

    def test_system_register_different_versions(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")

        plugin = create_plugin("test", "2.0.0", TestPluginV2)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")
        assert_system_running(self.easy_client, "test", "2.0.0")

    @pytest.mark.xfail(reason="Depends on beer-garden/bartender#7")
    def test_system_register_same_instance_name(self):
        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        start_plugin(plugin, self.easy_client)
        assert_system_running(self.easy_client, "test", "1.0.0")

        plugin = create_plugin("test", "1.0.0", TestPluginV1)
        with pytest.raises(ValidationError):
            self.easy_client.create_system(plugin.system)
