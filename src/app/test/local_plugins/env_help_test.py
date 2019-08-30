import os
import unittest

from bartender.local_plugins.env_help import (
    string_contains_environment_var,
    is_string_environment_variable,
    get_environment_var_name_from_string,
    expand_string_with_environment_var,
)


class EnvHelpTest(unittest.TestCase):
    def setUp(self):
        self.safe_copy = os.environ.copy()

    def tearDown(self):
        os.environ = self.safe_copy

    def test_string_contains_environment_var_no_dollar(self):
        self.assertEqual(string_contains_environment_var("foo"), False)

    def test_string_contains_environment_var_single_escaped(self):
        self.assertEqual(string_contains_environment_var(r"\$foo"), False)

    def test_string_contains_environment_var_multi_escaped(self):
        self.assertEqual(string_contains_environment_var(r"\$foo:\$bar"), False)

    def test_string_contains_environment_var_true(self):
        self.assertEqual(string_contains_environment_var("$FOO"), True)

    def test_string_contains_environment_var_embedded(self):
        self.assertEqual(string_contains_environment_var(r"\$foo:$BAR"), True)

    def test_string_contains_environment_var_bad_var(self):
        self.assertEqual(string_contains_environment_var("$.MyWeirdValue"), False)

    def test_string_contians_environmnet_var_embedded_2(self):
        self.assertEqual(string_contains_environment_var("foo:$BAR"), True)

    def test_string_contains_environment_var_embeeded_escape(self):
        self.assertEqual(string_contains_environment_var(r"foo\$bar"), False)

    def test_is_string_environment_variable_no_string(self):
        self.assertEqual(is_string_environment_variable(""), False)

    def test_is_string_environment_variable_first_character_not_alpha(self):
        self.assertEqual(is_string_environment_variable("8FOO"), False)

    def test_is_string_environmnet_variable_first_character_alpha(self):
        self.assertEqual(is_string_environment_variable("FOO"), True)

    def test_get_environment_var_name_from_string_empty_string(self):
        self.assertEqual(get_environment_var_name_from_string(""), "")

    def test_get_environment_var_name_from_string_just_good_values(self):
        self.assertEqual(get_environment_var_name_from_string("FOOBAR"), "FOOBAR")

    def test_get_environment_var_name_from_string_new_value(self):
        self.assertEqual(get_environment_var_name_from_string("FOO:BAR"), "FOO")

    def test_expand_string_with_environmnet_var_complex_no_environment_var(self):
        value = r"FOO_BAR:/path/to/something/el\$e"
        self.assertEqual(expand_string_with_environment_var(value), value)

    def test_expand_string_with_environment_var_simple_no_environment_var(self):
        value = "foo"
        self.assertEqual(expand_string_with_environment_var(value), value)

    def test_expand_string_with_environment_var_simple_environmnet_var(self):
        os.environ["FOO"] = "system_value"
        value = "$FOO"
        self.assertEqual(expand_string_with_environment_var(value), "system_value")

    def test_expand_string_with_environment_multi_environments_simple(self):
        os.environ["FOO"] = "/path/to/foo/bin"
        os.environ["BAR"] = "/path/to/bar/bin"
        value = "$FOO:$BAR"
        self.assertEqual(
            expand_string_with_environment_var(value),
            "/path/to/foo/bin:/path/to/bar/bin",
        )

    def test_expand_string_with_environmnent_mixed_with_dollars(self):
        os.environ["FOO"] = "/path/to/foo/bin"
        value = "/home/bin:$FOO"
        self.assertEqual(
            expand_string_with_environment_var(value), "/home/bin:/path/to/foo/bin"
        )

    def test_expand_string_with_environment_real_world_example(self):
        os.environ["JAVA_HOME"] = "/path/to/java"
        copy = os.environ.copy()
        original_path = copy["PATH"]
        value = "/path/to/my/bin:$JAVA_HOME/bin:$PATH"
        self.assertEqual(
            expand_string_with_environment_var(value),
            "/path/to/my/bin:/path/to/java/bin:" + original_path,
        )

    def test_expand_string_with_environment_bad_env_var(self):
        value = "Myp@$.word"
        self.assertEqual(expand_string_with_environment_var(value), value)
