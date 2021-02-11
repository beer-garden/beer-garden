import pytest
from mock import Mock

import beer_garden.filters.permission_mapper
import beer_garden.router


class TestPermissionMapper(object):

    def test_no_current_user(self):

        assert len(beer_garden.filters.permission_mapper.route_accesses.keys()) == \
               len(beer_garden.router.route_functions.keys())
