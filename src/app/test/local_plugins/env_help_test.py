# -*- coding: utf-8 -*-

import os
from contextlib import contextmanager

import pytest

from beer_garden.local_plugins.env_help import (
    string_contains_environment_var,
    is_string_environment_variable,
    get_environment_var_name_from_string,
    expand_string_with_environment_var,
)


@contextmanager
def mangle_env(updates):
    env_copy = os.environ.copy()
    for k, v in updates.items():
        os.environ[k] = v

    yield
    os.environ = env_copy


@pytest.mark.parametrize(
    "data,expected",
    [
        ("$FOO", True),  # Normal
        (r"\$foo:$BAR", True),  # Embedded
        ("foo:$BAR", True),  # Embedded 2
        ("", False),  # Empty string
        ("foo", False),  # No dollar
        (r"\$foo", False),  # Single escaped
        (r"\$foo:\$bar", False),  # Multi escaped
        ("$.MyWeirdValue", False),  # Bad variable
        (r"foo\$bar", False),  # Embedded escape
    ],
)
def test_string_contains_environment_var(data, expected):
    assert string_contains_environment_var(data) is expected


@pytest.mark.parametrize(
    "data,expected",
    [
        ("FOO", True),  # Normal
        ("", False),  # Empty string
        ("8FOO", False),  # First character numeric
    ],
)
def test_is_string_environment_variable(data, expected):
    assert is_string_environment_variable(data) is expected


@pytest.mark.parametrize(
    "data,expected",
    [
        ("", ""),  # Empty string
        ("FOOBAR", "FOOBAR"),  # Good values
        ("FOO:BAR", "FOO"),  # New value
    ],
)
def test_get_environment_var_name_from_string(data, expected):
    assert get_environment_var_name_from_string(data) == expected


@pytest.mark.parametrize(
    "data,expected,env_updates",
    [
        ("foo", "foo", {}),
        (r"FOO_BAR:/path/el\$e", r"FOO_BAR:/path/el\$e", {}),
        ("$FOO", "BAR", {"FOO": "BAR"}),
        ("$FOO:$BAR", "/path1:/path2", {"FOO": "/path1", "BAR": "/path2"}),
        ("/home/bin:$FOO", "/home/bin:/path1", {"FOO": "/path1"}),
        ("/bin:$JAVA_HOME", "/bin:/path/java", {"JAVA_HOME": "/path/java"}),
        ("Myp@$.word", "Myp@$.word", {}),
    ],
)
def test_expand_string_with_environment_var(data, expected, env_updates):
    with mangle_env(env_updates):
        assert expand_string_with_environment_var(data) == expected
