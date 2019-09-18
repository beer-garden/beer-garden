import copy

import brewtils.test
import pytest
from mongoengine import connect

from beer_garden.bg_utils.mongo.models import Instance
from beer_garden.bg_utils.mongo.parser import MongoParser
from test.bg_utils.unit.mongo import brew2mongo

pytest_plugins = ["brewtils.test.fixtures"]


# This is so the comparison helpers in brewtils.text.comparison to work correctly
def pytest_configure():
    setattr(brewtils.test, "_running_tests", True)


def pytest_unconfigure():
    delattr(brewtils.test, "_running_tests")


@pytest.fixture()
def mongo_conn():
    connect("beer_garden", host="mongomock://localhost")


@pytest.fixture
def bad_id():
    """A bad mongo ID"""
    return "".join(["1" for _ in range(24)])


# TODO - These should eventually not need to live outside the DB subsystem
@pytest.fixture
def mongo_system(bg_system):
    return brew2mongo(bg_system)


@pytest.fixture
def mongo_instance(instance_dict, ts_dt):
    """An instance as a model."""
    dict_copy = copy.deepcopy(instance_dict)
    dict_copy["status_info"]["heartbeat"] = ts_dt
    return Instance(**dict_copy)


@pytest.fixture
def mongo_job(bg_job):
    return brew2mongo(bg_job)


@pytest.fixture
def mongo_principal(principal_dict):
    principal = principal_dict.copy()
    del principal["permissions"]
    return MongoParser().parse_principal(principal, False)


@pytest.fixture
def mongo_role(role_dict):
    role = role_dict.copy()
    role["roles"] = []
    return MongoParser().parse_role(role, False)


@pytest.fixture
def mongo_bg_request(bg_request):
    return brew2mongo(bg_request)


@pytest.fixture
def mongo_parent_request(parent_request):
    return brew2mongo(parent_request)


@pytest.fixture
def mongo_child_request(child_request):
    return brew2mongo(child_request)


@pytest.fixture
def mongo_request_template(bg_request_template):
    return brew2mongo(bg_request_template)
