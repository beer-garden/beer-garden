import beer_garden.filters.db_filters

from brewtils.models import (
    Operation,
    Principal,
    Role,
    Permission,
)


class TestModelDbFilter(object):
    def test_add_one_filter(self):
        one_namespace = Principal(
            roles=[Role(permissions=[Permission(access="ADMIN", namespace="p")])]
        )
        model = Operation(operation_type="REQUEST_COUNT", kwargs={})

        beer_garden.filters.db_filters.model_db_filter(
            obj=model, current_user=one_namespace
        )

        assert len(model.kwargs["namespace__in"]) == 1

    def test_add_two_filters(self):
        two_namespaces = Principal(
            roles=[
                Role(
                    permissions=[
                        Permission(access="ADMIN", namespace="p"),
                        Permission(access="ADMIN", namespace="c"),
                    ]
                )
            ]
        )
        model = Operation(operation_type="REQUEST_COUNT", kwargs={})

        beer_garden.filters.db_filters.model_db_filter(
            obj=model, current_user=two_namespaces
        )

        assert len(model.kwargs["namespace__in"]) == 2

    def test_add_two_filters_with_existing(self):
        two_namespaces = Principal(
            roles=[
                Role(
                    permissions=[
                        Permission(access="ADMIN", namespace="p"),
                        Permission(access="ADMIN", namespace="c"),
                    ]
                )
            ]
        )
        model = Operation(
            operation_type="REQUEST_COUNT", kwargs={"namespace__in": ["e"]}
        )

        beer_garden.filters.db_filters.model_db_filter(
            obj=model, current_user=two_namespaces
        )

        assert len(model.kwargs["namespace__in"]) == 3

    def test_local(self):
        local = Principal(
            roles=[Role(permissions=[Permission(access="ADMIN", is_local=True)])]
        )

        model = Operation(operation_type="REQUEST_COUNT", kwargs={})

        beer_garden.filters.db_filters.model_db_filter(obj=model, current_user=local)

        assert "namespace__in" not in model.kwargs.keys()
