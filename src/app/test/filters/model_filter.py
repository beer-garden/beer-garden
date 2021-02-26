import pytest
from mock import Mock

from beer_garden.filters import model_filter
import beer_garden.filters.garden_namespace_mapper
from beer_garden.filters.permission_mapper import Permissions
from brewtils.errors import AuthorizationRequired

from brewtils.models import (
    BaseModel,
    Principal,
    Role,
    Permission,
)


@pytest.fixture
def filter_brewtils_model_mock(monkeypatch):
    mock = Mock(return_value=None)
    monkeypatch.setattr(model_filter, "filter_brewtils_model", mock)
    return mock


def _filter_brewtils_model_mock(monkeypatch, return_value=None):
    mock = Mock(return_value=return_value)
    monkeypatch.setattr(model_filter, "filter_brewtils_model", mock)
    return mock


@pytest.fixture
def config_get(monkeypatch, enabled=True):
    if enabled:
        mock = Mock(side_effect=config_get_side_effort_enabled)
    else:
        mock = Mock(side_effect=config_get_side_effort_disabled)

    monkeypatch.setattr(model_filter, "config.get", mock)

    return mock


def _config_get(monkeypatch, enabled=True):
    if enabled:
        mock = Mock(side_effect=config_get_side_effort_enabled)
    else:
        mock = Mock(side_effect=config_get_side_effort_disabled)

    monkeypatch.setattr(model_filter.config, "get", mock)

    return mock


def config_get_side_effort_enabled(value):
    if value == "garden.name":
        return "default"
    elif value == "auth.enabled":
        return True


def config_get_side_effort_disabled(value):
    if value == "garden.name":
        return "default"
    elif value == "auth.enabled":
        return False


def mock_obj():
    obj = BaseModel()
    obj.schema = "foo"

    return [obj]


def mock_principals(namespace, garden, access_level):
    garden_admin_principal = Principal(
        roles=[Role(permissions=[Permission(access="ADMIN", garden=garden)])]
    )

    garden_admin_access = (
        access_level
        in [
            Permissions.LOCAL_ADMIN,
            Permissions.ADMIN,
            Permissions.OPERATOR,
            Permissions.READ,
        ]
        and garden == "default"
    )

    garden_operator_principal = Principal(
        roles=[Role(permissions=[Permission(access="OPERATOR", garden=garden)])]
    )

    garden_operator_access = (
        access_level in [Permissions.OPERATOR, Permissions.READ] and garden == "default"
    )

    garden_read_principal = Principal(
        roles=[Role(permissions=[Permission(access="READ", garden=garden)])]
    )
    garden_read_access = access_level in [Permissions.READ] and garden == "default"

    namespace_p_admin_principal = Principal(
        roles=[Role(permissions=[Permission(access="ADMIN", namespace="p")])]
    )
    namespace_p_admin_access = (
        access_level in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
        and namespace == "p"
    )

    namespace_p_operator_principal = Principal(
        roles=[Role(permissions=[Permission(access="OPERATOR", namespace="p")])]
    )
    namespace_p_operator_access = (
        access_level in [Permissions.OPERATOR, Permissions.READ] and namespace == "p"
    )

    namespace_p_read_principal = Principal(
        roles=[Role(permissions=[Permission(access="READ", namespace="p")])]
    )
    namespace_p_read_access = access_level in [Permissions.READ] and namespace == "p"

    namespace_c_admin_principal = Principal(
        roles=[Role(permissions=[Permission(access="ADMIN", namespace="c")])]
    )
    namespace_c_admin_access = (
        access_level in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
        and namespace == "c"
    )

    namespace_c_operator_principal = Principal(
        roles=[Role(permissions=[Permission(access="OPERATOR", namespace="c")])]
    )
    namespace_c_operator_access = (
        access_level in [Permissions.OPERATOR, Permissions.READ] and namespace == "c"
    )

    namespace_c_read_principal = Principal(
        roles=[Role(permissions=[Permission(access="READ", namespace="c")])]
    )
    namespace_c_read_access = access_level in [Permissions.READ] and namespace == "c"
    mixed_p_principal = Principal(
        roles=[
            Role(permissions=[Permission(access="ADMIN", namespace="p")]),
            Role(permissions=[Permission(access="READ", namespace="c")]),
        ]
    )
    mixed_p_access = (
        access_level in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
        and namespace == "p"
    ) or (access_level in [Permissions.READ] and namespace == "c")

    mixed_c_principal = Principal(
        roles=[
            Role(permissions=[Permission(access="ADMIN", namespace="c")]),
            Role(permissions=[Permission(access="READ", namespace="p")]),
        ]
    )
    mixed_c_access = (
        access_level in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
        and namespace == "c"
    ) or (access_level in [Permissions.READ] and namespace == "0")

    return [
        (garden_admin_principal, garden_admin_access),
        (garden_operator_principal, garden_operator_access),
        (garden_read_principal, garden_read_access),
        (namespace_p_admin_principal, namespace_p_admin_access),
        (namespace_p_operator_principal, namespace_p_operator_access),
        (namespace_p_read_principal, namespace_p_read_access),
        (namespace_c_admin_principal, namespace_c_admin_access),
        (namespace_c_operator_principal, namespace_c_operator_access),
        (namespace_c_read_principal, namespace_c_read_access),
        (mixed_p_principal, mixed_p_access),
        (mixed_c_principal, mixed_c_access),
    ]


def build_access_mapper(namespace=None, garden=None):
    mapping = list()

    for permission in [
        Permissions.LOCAL_ADMIN,
        Permissions.ADMIN,
        Permissions.OPERATOR,
        Permissions.READ,
    ]:
        for principal, valid_access in mock_principals(namespace, garden, permission):
            mapping.append((namespace, garden, permission, principal, valid_access))

    return mapping


class TestPermissionCheck(object):
    @pytest.mark.parametrize(
        "namespace, garden, access_level, principal, valid_access",
        build_access_mapper(namespace="e"),
    )
    def test_e_namespace(
        self, namespace, garden, access_level, principal, valid_access, monkeypatch
    ):
        _config_get(monkeypatch)

        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            garden=garden,
            current_user=principal,
            required_permission=access_level,
        )

    @pytest.mark.parametrize(
        "namespace, garden, access_level, principal, valid_access",
        build_access_mapper(namespace="c"),
    )
    def test_c_namespace(
        self, namespace, garden, access_level, principal, valid_access, monkeypatch
    ):
        _config_get(monkeypatch)

        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            garden=garden,
            current_user=principal,
            required_permission=access_level,
        )

    @pytest.mark.parametrize(
        "namespace, garden, access_level, principal, valid_access",
        build_access_mapper(namespace="p"),
    )
    def test_p_namespace(
        self, namespace, garden, access_level, principal, valid_access, monkeypatch
    ):
        _config_get(monkeypatch)

        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            garden=garden,
            current_user=principal,
            required_permission=access_level,
        )

    @pytest.mark.parametrize(
        "namespace, garden, access_level, principal, valid_access",
        build_access_mapper(namespace="e", garden="default"),
    )
    def test_e_namespace_default_garden(
        self, namespace, garden, access_level, principal, valid_access, monkeypatch
    ):
        _config_get(monkeypatch)

        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            garden=garden,
            current_user=principal,
            required_permission=access_level,
        )

    @pytest.mark.parametrize(
        "namespace, garden, access_level, principal, valid_access",
        build_access_mapper(namespace="e", garden="child"),
    )
    def test_e_namespace_child_garden(
        self, namespace, garden, access_level, principal, valid_access, monkeypatch
    ):
        _config_get(monkeypatch)

        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            garden="default",
            current_user=principal,
            required_permission=access_level,
        )


class TestModelFilter(object):
    def test_no_permissions(self, filter_brewtils_model_mock, monkeypatch):
        _config_get(monkeypatch)

        model_filter.model_filter(required_permission=None)

        assert not filter_brewtils_model_mock.called

    def test_no_current_user(self, filter_brewtils_model_mock, monkeypatch):
        _config_get(monkeypatch, enabled=True)

        with pytest.raises(AuthorizationRequired):
            model_filter.model_filter(required_permission=Permissions.READ)

        assert not filter_brewtils_model_mock.called

    def test_single_obj_returned(self, monkeypatch):
        _filter_brewtils_model_mock(monkeypatch=monkeypatch, return_value={})
        _config_get(monkeypatch)

        assert (
            model_filter.model_filter(
                required_permission=Permissions.READ,
                current_user=Principal(
                    roles=[Role(permissions=[Permission(access="ADMIN")])]
                ),
                obj={},
            )
            == {}
        )

    def test_list_obj_returned(self, monkeypatch):
        _filter_brewtils_model_mock(monkeypatch=monkeypatch, return_value={"a": "b"})
        _config_get(monkeypatch)

        response = model_filter.model_filter(
            required_permission=Permissions.READ,
            current_user=Principal(
                roles=[Role(permissions=[Permission(access="ADMIN")])]
            ),
            obj=[{"a": "b"}],
        )

        assert response == [{"a": "b"}]

    def test_single_obj_filtered(self, filter_brewtils_model_mock, monkeypatch):
        _config_get(monkeypatch)
        assert (
            model_filter.model_filter(
                required_permission=Permissions.READ,
                current_user=Principal(
                    roles=[Role(permissions=[Permission(access="ADMIN")])]
                ),
                obj={},
            )
            is None
        )

    def test_list_obj_filtered(self, filter_brewtils_model_mock, monkeypatch):
        _config_get(monkeypatch)
        assert (
            model_filter.model_filter(
                required_permission=Permissions.READ,
                current_user=Principal(
                    roles=[Role(permissions=[Permission(access="ADMIN")])]
                ),
                obj=[{"a": "b"}],
            )
            == []
        )


class TestFilterBrewtilsModel(object):
    def test_no_schema_pass(self):
        response = model_filter.filter_brewtils_model(
            required_permission=Permissions.READ,
            current_user=Principal(
                roles=[Role(permissions=[Permission(access="ADMIN")])]
            ),
            obj={"a": "b"},
        )
        assert response == {"a": "b"}

    def test_no_schema_fail(self):
        response = model_filter.filter_brewtils_model(
            required_permission=Permissions.ADMIN,
            raise_error=False,
            current_user=Principal(
                roles=[Role(permissions=[Permission(access="READ")])]
            ),
            obj=[{"a": "b"}],
        )
        assert response is None

    def test_no_schema_fail_raise_error(self):
        with pytest.raises(AuthorizationRequired):
            model_filter.filter_brewtils_model(
                required_permission=Permissions.ADMIN,
                raise_error=True,
                current_user=Principal(
                    roles=[Role(permissions=[Permission(access="READ")])]
                ),
                obj=[{"a": "b"}],
            )

    @pytest.mark.parametrize("mock_obj", mock_obj())
    def test_namespace_foo_pass(self, monkeypatch, mock_obj):
        monkeypatch.setattr(
            beer_garden.filters.garden_namespace_mapper,
            "find_obj_garden_namespace",
            Mock(return_value=("default", "foo")),
        )

        response = model_filter.filter_brewtils_model(
            required_permission=Permissions.READ,
            current_user=Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", namespace="foo")])]
            ),
            obj=mock_obj,
        )
        assert response == mock_obj

    @pytest.mark.parametrize("mock_obj", mock_obj())
    def test_namespace_foo_fail(self, monkeypatch, mock_obj):
        monkeypatch.setattr(
            model_filter,
            "find_obj_garden_namespace",
            Mock(return_value=("default", "foo")),
        )

        response = model_filter.filter_brewtils_model(
            required_permission=Permissions.READ,
            raise_error=False,
            current_user=Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", namespace="bar")])]
            ),
            obj=mock_obj,
        )

        assert response is None

    @pytest.mark.parametrize("mock_obj", mock_obj())
    def test_namespace_foo_fail_raise_error(self, monkeypatch, mock_obj):
        monkeypatch.setattr(
            model_filter,
            "find_obj_garden_namespace",
            Mock(return_value=("default", "foo")),
        )

        with pytest.raises(AuthorizationRequired):
            model_filter.filter_brewtils_model(
                required_permission=Permissions.READ,
                raise_error=True,
                current_user=Principal(
                    roles=[
                        Role(permissions=[Permission(access="ADMIN", namespace="bar")])
                    ]
                ),
                obj=mock_obj,
            )
