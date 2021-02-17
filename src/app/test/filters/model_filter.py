import pytest
from mock import Mock

from beer_garden.filters import model_filter
import beer_garden.filters.namespace_mapper
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


def mock_obj():
    obj = BaseModel()
    obj.schema = "foo"

    return [obj]


def mock_principals(namespace, access_level):
    return [
        (
            Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", is_local=True)])]
            ),
            access_level
            in [
                Permissions.LOCAL_ADMIN,
                Permissions.ADMIN,
                Permissions.OPERATOR,
                Permissions.READ,
            ],
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="OPERATOR", is_local=True)])]
            ),
            access_level in [Permissions.OPERATOR, Permissions.READ],
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="READ", is_local=True)])]
            ),
            access_level in [Permissions.READ],
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", namespace="p")])]
            ),
            access_level in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
            and namespace == "p",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="OPERATOR", namespace="p")])]
            ),
            access_level in [Permissions.OPERATOR, Permissions.READ]
            and namespace == "p",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="READ", namespace="p")])]
            ),
            access_level in [Permissions.READ] and namespace == "p",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="ADMIN", namespace="c")])]
            ),
            access_level in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
            and namespace == "c",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="OPERATOR", namespace="c")])]
            ),
            access_level in [Permissions.OPERATOR, Permissions.READ]
            and namespace == "c",
        ),
        (
            Principal(
                roles=[Role(permissions=[Permission(access="READ", namespace="c")])]
            ),
            access_level in [Permissions.READ] and namespace == "c",
        ),
        (
            Principal(
                roles=[
                    Role(permissions=[Permission(access="ADMIN", namespace="p")]),
                    Role(permissions=[Permission(access="READ", namespace="c")]),
                ]
            ),
            (
                access_level
                in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
                and namespace == "p"
            )
            or (access_level in [Permissions.READ] and namespace == "c"),
        ),
        (
            Principal(
                roles=[
                    Role(permissions=[Permission(access="ADMIN", namespace="c")]),
                    Role(permissions=[Permission(access="READ", namespace="p")]),
                ]
            ),
            (
                access_level
                in [Permissions.ADMIN, Permissions.OPERATOR, Permissions.READ]
                and namespace == "c"
            )
            or (access_level in [Permissions.READ] and namespace == "p"),
        ),
    ]


def build_access_mapper(namespace):
    mapping = list()

    for permission in [
        Permissions.LOCAL_ADMIN,
        Permissions.ADMIN,
        Permissions.OPERATOR,
        Permissions.READ,
    ]:
        for principal, valid_access in mock_principals(namespace, permission):
            mapping.append((namespace, permission, principal, valid_access))

    return mapping


class TestPermissionCheck(object):
    @pytest.mark.parametrize(
        "namespace, access_level, principal, valid_access", build_access_mapper("e")
    )
    def test_e_namespace(self, namespace, access_level, principal, valid_access):
        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            current_user=principal,
            required_permission=access_level,
        )

    @pytest.mark.parametrize(
        "namespace, access_level, principal, valid_access", build_access_mapper("c")
    )
    def test_c_namespace(self, namespace, access_level, principal, valid_access):
        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            current_user=principal,
            required_permission=access_level,
        )

    @pytest.mark.parametrize(
        "namespace, access_level, principal, valid_access", build_access_mapper("p")
    )
    def test_p_namespace(self, namespace, access_level, principal, valid_access):
        assert valid_access == model_filter.permission_check(
            namespace=namespace,
            current_user=principal,
            required_permission=access_level,
        )


class TestModelFilter(object):

    def test_no_permissions(self, filter_brewtils_model_mock):
        model_filter.model_filter(required_permission=None)

        assert not filter_brewtils_model_mock.called

    def test_no_current_user(self, filter_brewtils_model_mock):
        with pytest.raises(AuthorizationRequired):
            model_filter.model_filter(required_permission=Permissions.READ)

        assert not filter_brewtils_model_mock.called

    def test_local_admin(self):
        assert model_filter.model_filter(required_permission=Permissions.READ,
                                         current_user=Principal(
                                             roles=[Role(permissions=[
                                                 Permission(access="ADMIN", is_local=True)])]
                                         ), obj={}) is not None

    def test_single_obj_returned(self, monkeypatch):
        mock = _filter_brewtils_model_mock(monkeypatch=monkeypatch, return_value={})

        assert model_filter.model_filter(required_permission=Permissions.READ,
                                         current_user=Principal(
                                             roles=[Role(permissions=[
                                                 Permission(access="ADMIN")])]
                                         ), obj={}) == {}

    def test_list_obj_returned(self, monkeypatch):
        mock = _filter_brewtils_model_mock(monkeypatch=monkeypatch,
                                           return_value={'a': 'b'})

        assert model_filter.model_filter(required_permission=Permissions.READ,
                                         current_user=Principal(
                                             roles=[Role(permissions=[
                                                 Permission(access="ADMIN")])]
                                         ), obj=[{'a': 'b'}]) == [{'a': 'b'}]

    def test_single_obj_filtered(self, filter_brewtils_model_mock):
        assert model_filter.model_filter(required_permission=Permissions.READ,
                                         current_user=Principal(
                                             roles=[Role(permissions=[
                                                 Permission(access="ADMIN")])]
                                         ), obj={}) is None

    def test_list_obj_filtered(self, filter_brewtils_model_mock):
        assert model_filter.model_filter(required_permission=Permissions.READ,
                                         current_user=Principal(
                                             roles=[Role(permissions=[
                                                 Permission(access="ADMIN")])]
                                         ), obj=[{'a': 'b'}]) == []


class TestFilterBrewtilsModel(object):

    def test_no_schema_pass(self):
        assert model_filter.filter_brewtils_model(required_permission=Permissions.READ,
                                                  current_user=Principal(
                                                      roles=[Role(permissions=[
                                                          Permission(access="ADMIN")])]
                                                  ),
                                                  obj={'a': 'b'}) == {'a': 'b'}

    def test_no_schema_fail(self):
        assert model_filter.filter_brewtils_model(required_permission=Permissions.ADMIN,
                                                  raise_error=False,
                                                  current_user=Principal(
                                                      roles=[Role(permissions=[
                                                          Permission(access="READ")])]
                                                  ),
                                                  obj=[{'a': 'b'}]) is None

    def test_no_schema_fail_raise_error(self):
        with pytest.raises(AuthorizationRequired):
            model_filter.filter_brewtils_model(required_permission=Permissions.ADMIN,
                                               raise_error=True,
                                               current_user=Principal(
                                                   roles=[Role(permissions=[
                                                       Permission(access="READ")])]
                                               ),
                                               obj=[{'a': 'b'}])

    @pytest.mark.parametrize(
        "mock_obj", mock_obj()
    )
    def test_namespace_foo_pass(self, monkeypatch, mock_obj):
        monkeypatch.setattr(
            beer_garden.filters.namespace_mapper, "find_obj_namespace", Mock(return_value="foo")
        )

        assert model_filter.filter_brewtils_model(required_permission=Permissions.READ,
                                                  current_user=Principal(
                                                      roles=[Role(permissions=[
                                                          Permission(access="ADMIN",
                                                                     namespace="foo")])]
                                                  ),
                                                  obj=mock_obj) == mock_obj

    @pytest.mark.parametrize(
        "mock_obj", mock_obj()
    )
    def test_namespace_foo_fail(self, monkeypatch, mock_obj):
        monkeypatch.setattr(
            model_filter, "find_obj_namespace", Mock(return_value="foo")
        )

        assert model_filter.filter_brewtils_model(required_permission=Permissions.READ,
                                                  raise_error=False,
                                                  current_user=Principal(
                                                      roles=[Role(permissions=[
                                                          Permission(access="ADMIN",
                                                                     namespace="bar")])]
                                                  ),
                                                  obj=mock_obj) is None

    @pytest.mark.parametrize(
        "mock_obj", mock_obj()
    )
    def test_namespace_foo_fail_raise_error(self, monkeypatch, mock_obj):
        monkeypatch.setattr(
            model_filter, "find_obj_namespace", Mock(return_value="foo")
        )

        with pytest.raises(AuthorizationRequired):
            model_filter.filter_brewtils_model(required_permission=Permissions.READ,
                                               raise_error=True,
                                               current_user=Principal(
                                                   roles=[Role(permissions=[
                                                       Permission(access="ADMIN",
                                                                  namespace="bar")])]
                                               ),
                                               obj=mock_obj)
