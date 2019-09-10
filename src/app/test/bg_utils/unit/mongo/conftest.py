import copy

import pytest

from beer_garden.bg_utils.mongo.models import Instance


@pytest.fixture
def mongo_instance(instance_dict, ts_dt):
    """An instance as a model."""
    dict_copy = copy.deepcopy(instance_dict)
    dict_copy["status_info"]["heartbeat"] = ts_dt
    return Instance(**dict_copy)
