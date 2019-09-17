import logging
import os
import copy
import unittest

from mock import call, patch, Mock

from beer_garden.local_plugins.loader import LocalPluginLoader


class PluginLoaderTest(unittest.TestCase):
    def setUp(self):

        self.default_config = {
            "NAME": "foo",
            "VERSION": "1.0",
            "PLUGIN_ENTRY": "main.py",
            "INSTANCES": ["default"],
            "PLUGIN_ARGS": {"default": None},
            "REQUIRES": [],
            "METADATA": {},
            "ENVIRONMENT": {},
            "LOG_LEVEL": "INFO",
        }

        self.mock_validator = Mock()
        self.mock_registry = Mock()
        self.plugin_path = "/path/to/plugins"

        system_patcher = patch("beer_garden.local_plugins.loader.System")
        self.addCleanup(system_patcher.stop)
        self.system_mock = system_patcher.start()
        self.system_mock.find_unique = Mock(return_value=None)

        # config_patcher = patch("beer_garden.config")
        # self.addCleanup(config_patcher.stop)
        # self.config_mock = config_patcher.start()
        # self.config_mock.plugin.local.directory = self.plugin_path
        # self.config_mock.plugin.local.log_directory = None

        self.loader = LocalPluginLoader(self.mock_validator, self.mock_registry)

    @patch(
        "beer_garden.local_plugins.loader.LocalPluginLoader.scan_plugin_path",
        Mock(return_value=["pl1", "pl2"]),
    )
    @patch(
        "beer_garden.local_plugins.loader.LocalPluginLoader.validate_plugin_requirements"
    )
    @patch("beer_garden.local_plugins.loader.LocalPluginLoader.load_plugin")
    def test_load_plugins(self, load_plugin_mock, validate_mock):
        self.loader.load_plugins()
        load_plugin_mock.assert_has_calls([call("pl1"), call("pl2")], any_order=False)
        validate_mock.assert_called_once_with()

    @patch(
        "beer_garden.local_plugins.loader.LocalPluginLoader.scan_plugin_path",
        Mock(return_value=[]),
    )
    @patch(
        "beer_garden.local_plugins.loader.LocalPluginLoader.validate_plugin_requirements"
    )
    @patch("beer_garden.local_plugins.loader.LocalPluginLoader.load_plugin")
    def test_load_plugins_empty(self, load_plugin_mock, validate_mock):
        self.loader.load_plugins()
        self.assertFalse(load_plugin_mock.called)
        validate_mock.assert_called_once_with()

    @patch(
        "beer_garden.local_plugins.loader.LocalPluginLoader.scan_plugin_path",
        Mock(return_value=["pl1", "pl2"]),
    )
    @patch(
        "beer_garden.local_plugins.loader.LocalPluginLoader.validate_plugin_requirements"
    )
    @patch("beer_garden.local_plugins.loader.LocalPluginLoader.load_plugin")
    def test_load_plugins_exception(self, load_plugin_mock, validate_mock):
        load_plugin_mock.side_effect = [ValueError()]
        self.loader.load_plugins()
        load_plugin_mock.assert_has_calls([call("pl1"), call("pl2")], any_order=False)
        validate_mock.assert_called_once_with()

    @patch(
        "beer_garden.local_plugins.loader.listdir",
        Mock(return_value=["file1", "file2"]),
    )
    @patch("beer_garden.local_plugins.loader.isfile", Mock(side_effect=[False, True]))
    @patch("beer_garden.local_plugins.loader.LocalPluginLoader.load_plugin", Mock())
    def test_scan_plugin_path(self):
        self.assertEqual(
            [os.path.join(self.plugin_path, "file1")],
            self.loader.scan_plugin_path(path=self.plugin_path),
        )

    @patch("beer_garden.local_plugins.loader.listdir", Mock(return_value=[]))
    def test_scan_plugin_path_empty(self):
        self.assertEqual([], self.loader.scan_plugin_path(path=self.plugin_path))

    def test_scan_plugin_path_no_path(self):
        self.assertEqual([], self.loader.scan_plugin_path())

    def test_validate_plugin_requirements_no_plugins(self):
        self.mock_registry.get_all_plugins = Mock(return_value=[])
        self.assertEqual(self.mock_registry.remove.call_count, 0)

    def test_validate_plugin_requirements_no_requirements(self):
        self.mock_registry.get_all_plugins = Mock(
            return_value=[
                Mock(requirements=[], plugin_name="foo"),
                Mock(requirements=[], plugin_name="bar"),
            ]
        )
        self.loader.validate_plugin_requirements()
        self.assertEqual(self.mock_registry.remove.call_count, 0)

    def test_validate_plugin_requirements_good_requirements(self):
        self.mock_registry.get_all_plugins = Mock(
            return_value=[
                Mock(requirements=[], plugin_name="foo"),
                Mock(requirements=["foo"], plugin_name="bar"),
            ]
        )
        self.mock_registry.get_unique_plugin_names = Mock(return_value=["foo", "bar"])
        self.loader.validate_plugin_requirements()
        self.assertEqual(self.mock_registry.remove.call_count, 0)

    def test_validate_plugin_requirements_not_found(self):
        self.mock_registry.get_all_plugins = Mock(
            return_value=[
                Mock(requirements=[], plugin_name="foo"),
                Mock(requirements=["NOT_FOUND"], plugin_name="bar", unique_name="bar"),
            ]
        )
        self.mock_registry.get_unique_plugin_names = Mock(return_value=["foo", "bar"])
        self.loader.validate_plugin_requirements()
        self.assertEqual(self.mock_registry.remove.call_count, 1)
        self.mock_registry.remove.assert_called_with("bar")

    @patch("beer_garden.local_plugins.loader.LocalPluginLoader._load_plugin_config")
    def test_load_plugin(self, config_mock):
        config_mock.return_value = self.default_config
        self.mock_registry.plugin_exists = Mock(return_value=False)
        self.mock_validator.validate_plugin = Mock(return_value=True)

        self.assertTrue(self.loader.load_plugin("/path/to/foo-0.1"))
        self.assertTrue(self.mock_registry.register_plugin.called)

    @patch("beer_garden.local_plugins.loader.LocalPluginLoader._load_plugin_config")
    def test_load_plugin_already_exists(self, config_mock):
        config_mock.return_value = self.default_config
        self.mock_registry.plugin_exists = Mock(return_value=False)
        self.mock_validator.validate_plugin = Mock(return_value=True)

        plugin_mock = Mock(name="plugin_mock")
        self.system_mock.find_unique = Mock(return_value=plugin_mock)

        self.assertTrue(self.loader.load_plugin("/path/to/foo-0.1"))
        self.assertTrue(self.mock_registry.register_plugin.called)
        self.assertTrue(plugin_mock.delete_instances.called)

    @patch("beer_garden.local_plugins.loader.LocalPluginLoader._load_plugin_config")
    def test_load_plugin_multiple_instances(self, config_mock):
        config = copy.deepcopy(self.default_config)
        config["INSTANCES"] = ["i1", "i2"]
        config["PLUGIN_ARGS"] = {"i1": [], "i2": []}

        config_mock.return_value = config
        self.mock_registry.plugin_exists = Mock(return_value=False)
        self.mock_validator.validate_plugin = Mock(return_value=True)

        self.assertTrue(self.loader.load_plugin("/path/to/foo-0.1"))
        self.assertEqual(2, self.mock_registry.register_plugin.call_count)

    def test_load_plugin_invalid_plugin(self):
        self.mock_validator.validate_plugin = Mock(return_value=False)
        self.assertFalse(self.loader.load_plugin("path/to/foo-0.1"))

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_all_attributes(self, load_source_mock, sys_mock):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock()
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)
        load_source_mock.assert_called_once_with(module_name, path_mock)
        self.assertNotIn(module_name, sys_mock.modules)
        self.assertEqual(
            config,
            {
                "NAME": config_mock.NAME,
                "VERSION": config_mock.VERSION,
                "PLUGIN_ENTRY": config_mock.PLUGIN_ENTRY,
                "DESCRIPTION": config_mock.DESCRIPTION,
                "ICON_NAME": config_mock.ICON_NAME,
                "DISPLAY_NAME": config_mock.DISPLAY_NAME,
                "REQUIRES": config_mock.REQUIRES,
                "ENVIRONMENT": config_mock.ENVIRONMENT,
                "INSTANCES": config_mock.INSTANCES,
                "METADATA": config_mock.METADATA,
                "PLUGIN_ARGS": config_mock.PLUGIN_ARGS,
                "LOG_LEVEL": logging.INFO,
            },
        )

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_only_required_attributes(
        self, load_source_mock, sys_mock
    ):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(spec=["NAME", "VERSION", "PLUGIN_ENTRY"])
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)
        load_source_mock.assert_called_once_with(module_name, path_mock)
        self.assertNotIn(module_name, sys_mock.modules)
        self.assertEqual(
            config,
            {
                "NAME": config_mock.NAME,
                "VERSION": config_mock.VERSION,
                "PLUGIN_ENTRY": config_mock.PLUGIN_ENTRY,
                "DESCRIPTION": "",
                "ICON_NAME": None,
                "DISPLAY_NAME": None,
                "REQUIRES": [],
                "ENVIRONMENT": {},
                "INSTANCES": ["default"],
                "METADATA": {},
                "PLUGIN_ARGS": {"default": None},
                "LOG_LEVEL": logging.INFO,
            },
        )

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_instances_provided_no_plugin_args(
        self, load_source_mock, sys_mock
    ):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=["instance1", "instance2"],
            PLUGIN_ARGS=None,
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
        )
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)

        self.assertEqual(config["INSTANCES"], ["instance1", "instance2"])
        self.assertEqual(config["PLUGIN_ARGS"], {"instance1": None, "instance2": None})

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_plugin_args_list_provided_no_instances(
        self, load_source_mock, sys_mock
    ):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=None,
            PLUGIN_ARGS=["arg1"],
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
        )
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)

        self.assertEqual(config["INSTANCES"], ["default"])
        self.assertEqual(config["PLUGIN_ARGS"], {"default": ["arg1"]})

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_plugin_args_dict_no_instances(
        self, load_source_mock, sys_mock
    ):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=None,
            PLUGIN_ARGS={"foo": ["arg1"], "bar": ["arg2"]},
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
        )
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)

        expected = ["foo", "bar"]
        self.assertTrue(len(config["INSTANCES"]) == len(expected))
        self.assertTrue(sorted(config["INSTANCES"]) == sorted(expected))
        self.assertEqual(config["PLUGIN_ARGS"], {"foo": ["arg1"], "bar": ["arg2"]})

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_invalid_plugin_args(self, load_source_mock, sys_mock):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=None,
            PLUGIN_ARGS="invalid",
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
        )
        load_source_mock.return_value = config_mock

        self.assertRaises(ValueError, self.loader._load_plugin_config, path_mock)

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_instance_and_args_provided_args_list(
        self, load_source_mock, sys_mock
    ):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=["foo", "bar"],
            PLUGIN_ARGS=["arg1"],
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
        )
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)

        expected = ["foo", "bar"]
        self.assertTrue(len(config["INSTANCES"]) == len(expected))
        self.assertTrue(sorted(config["INSTANCES"]) == sorted(expected))
        self.assertEqual(config["PLUGIN_ARGS"], {"foo": ["arg1"], "bar": ["arg1"]})

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_log_level(self, load_source_mock, sys_mock):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=["foo", "bar"],
            PLUGIN_ARGS=["arg1"],
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
            LOG_LEVEL="DEBUG",
        )
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)
        self.assertEqual(config["LOG_LEVEL"], logging.DEBUG)

    @patch("beer_garden.local_plugins.loader.sys")
    @patch("beer_garden.local_plugins.loader.load_source")
    def test_load_plugin_config_log_level_bad(self, load_source_mock, sys_mock):
        module_name = "BGPLUGINCONFIG"
        sys_mock.modules = {module_name: ""}

        path_mock = Mock()
        config_mock = Mock(
            INSTANCES=["foo", "bar"],
            PLUGIN_ARGS=["arg1"],
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/file",
            LOG_LEVEL="INVALID",
        )
        load_source_mock.return_value = config_mock

        config = self.loader._load_plugin_config(path_mock)
        self.assertEqual(config["LOG_LEVEL"], logging.INFO)
