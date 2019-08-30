import os
import sys
import unittest

from mock import patch, Mock

from bartender.errors import PluginValidationError
from bartender.local_plugins.validator import LocalPluginValidator


class LocalPluginValidatorTest(unittest.TestCase):
    def setUp(self):
        self.validator = LocalPluginValidator()

    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_path",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_config",
        Mock(),
    )
    def test_validate_plugin_calls(self):
        rv = self.validator.validate_plugin("/path/to/plugin")
        self.assertEqual(self.validator.validate_plugin_path.call_count, 1)
        self.assertEqual(self.validator.validate_plugin_config.call_count, 1)
        self.assertEqual(rv, True)

    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_path",
        Mock(side_effect=PluginValidationError("foo")),
    )
    def test_validate_plugin_error(self):
        rv = self.validator.validate_plugin("/path/to/plugin")
        self.assertEqual(rv, False)

    @patch("bartender.local_plugins.validator.isfile", Mock(return_value=True))
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_path",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_entry_point",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_instances_and_args",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_environment",
        Mock(),
    )
    @patch("bartender.local_plugins.validator.load_source")
    def test_validate_plugin_load_plugin_config(self, mock_load):
        mock_load.return_value = {}
        self.validator.validate_plugin("/path/to/plugin")
        mock_load.assert_called_with(
            "BGPLUGINCONFIG", "/path/to/plugin/%s" % self.validator.CONFIG_NAME
        )

    @patch("bartender.local_plugins.validator.isfile", Mock(return_value=True))
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_path",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_entry_point",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_instances_and_args",
        Mock(),
    )
    @patch(
        "bartender.local_plugins.validator.LocalPluginValidator.validate_plugin_environment",
        Mock(),
    )
    @patch("bartender.local_plugins.validator.load_source")
    def test_validate_remove_plugin_config_from_sys_modules(self, mock_load):
        def side_effect(module_name, value):
            sys.modules[module_name] = value

        mock_load.side_effect = side_effect
        self.validator.validate_plugin("/path/to/plugin")
        self.assertNotIn("BGPLUGINCONFIG", sys.modules)

    def test_validate_plugin_path_bad(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_plugin_path,
            "/path/to/non-existant/foo",
        )

    def test_validate_plugin_path_none(self):
        self.assertRaises(
            PluginValidationError, self.validator.validate_plugin_path, None
        )

    def test_validate_plugin_path_good(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.assertTrue(self.validator.validate_plugin_path(current_directory))

    def test_validate_plugin_config_none(self):
        self.assertRaises(
            PluginValidationError, self.validator.validate_plugin_config, None
        )

    @patch("bartender.local_plugins.validator.isfile")
    def test_validate_plugin_config_not_a_file(self, isfile_mock):
        isfile_mock.return_value = False
        self.assertRaises(
            PluginValidationError, self.validator.validate_plugin_config, "not_a_file"
        )
        isfile_mock.assert_called_with("not_a_file/%s" % self.validator.CONFIG_NAME)

    def test_validate_entry_point_none_config_module(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_entry_point,
            None,
            "/path/to/plugin",
        )

    def test_validate_entry_point_none_path_to_plugin(self):
        self.assertRaises(
            PluginValidationError, self.validator.validate_entry_point, {}, None
        )

    def test_validate_entry_point_no_entry_point_key(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_entry_point,
            Mock(spec=[]),
            "/path/to/plugin",
        )

    def test_validate_entry_point_bad_entry_point(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_entry_point,
            Mock(spec=[self.validator.ENTRY_POINT_KEY], PLUGIN_ENTRY="not_a_file"),
            "/path/to/plugin",
        )

    @patch("bartender.local_plugins.validator.isfile", Mock(return_value=True))
    def test_validate_entry_point_good_file(self):
        self.validator.validate_entry_point(
            Mock(PLUGIN_ENTRY="is_totally_a_file"), "/path/to/plugin"
        )

    @patch("bartender.local_plugins.validator.isdir", Mock(return_value=True))
    @patch("bartender.local_plugins.validator.isfile")
    def test_validate_entry_point_good_package(self, isfile_mock):
        def is_special_file(name):
            return "__init__" in name or "__main__" in name

        isfile_mock.side_effect = is_special_file

        self.validator.validate_entry_point(
            Mock(PLUGIN_ENTRY="-m plugin"), "/path/to/plugin"
        )

    def test_validate_individual_plugin_arguments_not_none_or_list(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_individual_plugin_arguments,
            "notalistornone",
        )

    def test_validate_individual_plugin_arguments_none(self):
        self.assertTrue(self.validator.validate_individual_plugin_arguments(None))

    def test_validate_individual_plugin_arguments_bad_list(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_individual_plugin_arguments,
            [{"foo": "bar"}],
        )

    def test_validate_individual_plugin_arguments_good_list(self):
        self.assertTrue(self.validator.validate_individual_plugin_arguments(["good"]))

    def test_validate_plugin_environment_none_config(self):
        self.assertRaises(
            PluginValidationError, self.validator.validate_plugin_environment, None
        )

    def test_validate_plugin_environment_no_environment(self):
        self.assertTrue(self.validator.validate_plugin_environment(Mock(spec=[])))

    def test_validate_plugin_environment_bad_environment(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_plugin_environment,
            Mock(ENVIRONMENT="notadict"),
        )

    def test_validate_plugin_environment_bad_key(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_plugin_environment,
            Mock(ENVIRONMENT={1: "int_key_not_allowed"}),
        )

    def test_validate_plugin_environment_with_bg_prefix_key(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_plugin_environment,
            Mock(ENVIRONMENT={"BG_foo": "that_key_is_not_allowed"}),
        )

    def test_validate_plugin_environment_bad_value(self):
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_plugin_environment,
            Mock(ENVIRONMENT={"foos": ["foo1", "foo2"]}),
        )

    def test_validate_plugin_environment_good(self):
        self.assertTrue(
            self.validator.validate_plugin_environment(Mock(ENVIRONMENT={"foo": "bar"}))
        )

    @patch("bartender.local_plugins.validator.isfile", Mock(return_value=True))
    @patch("bartender.local_plugins.validator.LocalPluginValidator._load_plugin_config")
    def test_validate_plugin_config_missing_required_key(self, load_config_mock):
        config_module = Mock(
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/entry.py",
            spec=["VERSION", "PLUGIN_ENTRY"],
        )
        load_config_mock.return_value = config_module
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_plugin_config,
            "/path/to/beer.conf",
        )

    @patch("bartender.local_plugins.validator.isfile", Mock(return_value=True))
    @patch("bartender.local_plugins.validator.LocalPluginValidator._load_plugin_config")
    def test_validate_plugin_config_good(self, load_config_mock):
        config_module = Mock(
            NAME="name",
            VERSION="0.0.1",
            PLUGIN_ENTRY="/path/to/entry.py",
            spec=["NAME", "VERSION", "PLUGIN_ENTRY"],
        )
        load_config_mock.return_value = config_module
        self.assertTrue(self.validator.validate_plugin_config("/path/to/beer.conf"))

    def test_validate_instances_and_args_none_config_module(self):
        self.assertRaises(
            PluginValidationError, self.validator.validate_instances_and_args, None
        )

    def test_validate_instances_and_args_both_none(self):
        config_module = Mock(spec=[])
        self.assertTrue(
            PluginValidationError,
            self.validator.validate_instances_and_args(config_module),
        )

    def test_validate_instances_and_args_invalid_instances(self):
        config_module = Mock(INSTANCES="THIS_IS_WRONG", PLUGIN_ARGS=None)
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_instances_and_args,
            config_module,
        )

    def test_validate_instances_and_args_good_args(self):
        config_module = Mock(INSTANCES=None, PLUGIN_ARGS=["foo", "bar"])
        self.assertTrue(self.validator.validate_instances_and_args(config_module))

    def test_validate_instances_and_args_invalid_args(self):
        config_module = Mock(INSTANCES=None, PLUGIN_ARGS="THIS IS WRONG")
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_instances_and_args,
            config_module,
        )

    def test_validate_instances_and_args_invalid_plugin_arg_key(self):
        config_module = Mock(INSTANCES=["foo"], PLUGIN_ARGS={"bar": ["arg1"]})
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_instances_and_args,
            config_module,
        )

    def test_validate_instances_and_args_missing_plugin_arg_key(self):
        config_module = Mock(INSTANCES=["foo"], PLUGIN_ARGS={})
        self.assertRaises(
            PluginValidationError,
            self.validator.validate_instances_and_args,
            config_module,
        )

    def test_validate_instance_and_args_both_provided_good(self):
        config_module = Mock(INSTANCES=["foo"], PLUGIN_ARGS={"foo": ["arg1"]})
        self.assertTrue(self.validator.validate_instances_and_args(config_module))
