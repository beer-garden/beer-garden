import beer_garden.filters.permission_mapper
import beer_garden.router


class TestPermissionMapper(object):
    def test_router_and_permission_mapping(self):
        assert len(beer_garden.filters.permission_mapper.route_accesses.keys()) == len(
            beer_garden.router.route_functions.keys()
        )

    def test_permission_mapping(self, bg_operation):
        bg_operation.operation_type = "REQUEST_READ"

        assert (
            beer_garden.filters.permission_mapper.determine_permission(bg_operation)
            == beer_garden.filters.permission_mapper.Permissions.READ
        )

    def test_permission_mapping_fail(self, bg_operation):
        bg_operation.operation_type = "REQUEST_READ_BAD"

        assert (
            beer_garden.filters.permission_mapper.determine_permission(bg_operation)
            is None
        )
