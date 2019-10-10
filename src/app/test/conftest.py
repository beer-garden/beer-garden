import copy

import brewtils.test
import pytest
from mongoengine import connect

import beer_garden

pytest_plugins = ["brewtils.test.fixtures"]


def pytest_configure():
    # This is so the comparison helpers in brewtils.text.comparison to work correctly
    setattr(brewtils.test, "_running_tests", True)
    setattr(beer_garden, "_running_tests", True)


def pytest_unconfigure():
    delattr(brewtils.test, "_running_tests")
    delattr(beer_garden, "_running_tests")


@pytest.fixture()
def mongo_conn():
    connect("beer_garden", host="mongomock://localhost")


@pytest.fixture
def bad_id():
    """A bad mongo ID"""
    return "".join(["1" for _ in range(24)])
