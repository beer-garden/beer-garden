# -*- coding: utf-8 -*-

import os
from typing import Dict


def has_env_var(string: str) -> bool:
    """Determines whether or not there is a valid environment variable in the string"""
    parts = string.split("$")

    # If there's no $ then there's no possibility of an environment variable
    if len(parts) == 1:
        return False

    for index, part in enumerate(parts):
        # If the part has no length then the first variable is an unescaped
        # $ and we will just continue as it could be an invalid var such as $%
        # Also, if the first character is not an alpha then this part is invalid
        if not is_valid_name(part):
            continue

        if index > 0:
            # If we are not on the first element, then we check to see if the previous
            # entry ended in a "\" if it did, then that means this value should have a
            # literal dollar sign in it so we just continue
            # i.e.  foo\$bar
            prev_part = parts[index - 1]
            if prev_part.endswith("\\"):
                continue

            # otherwise we've found a valid environment variable
            else:
                return True

        # If we are on the first element, and it does not end with a "\" and it is not
        # the last element in the array then we must have an environment variable
        # i.e.  /path/to/foo:$PATH
        elif not part.endswith("\\") and index + 1 != len(parts):
            return True

    return False


def is_valid_name(string: str) -> bool:
    """Determine if a string is a valid environment variable"""
    if len(string) == 0:
        return False

    return string[0].isalpha()


def var_name(string: str) -> str:
    """Strips out the Variable name from a string
    :param string: e.g. $MY_PATH:$YOUR_PATH
    :return string: e.g. MY_PATH
    """
    key = ""
    for char in string:
        if char.isalpha() or char.isdigit() or char == "_":
            key += char
        else:
            return key

    return key


def expand_string(string: str, env_copy: Dict[str, str] = None) -> str:
    """Expands a String with a $VAR style var in it."""
    parts = string.split("$")
    if env_copy is None:
        env_copy = os.environ.copy()

    expanded_value = ""
    for index, part in enumerate(parts):
        if index == 0:
            if len(part) == 0:
                continue
            else:
                expanded_value += part

        elif expanded_value.endswith("\\"):
            expanded_value += "$" + part

        elif is_valid_name(part):
            environment_key = var_name(part)
            environment_value = env_copy.get(environment_key, "")
            expanded_value += part.replace(environment_key, environment_value)
        else:
            expanded_value += "$" + part

    return expanded_value
