import pytest
from mock import Mock

from beer_garden.filters import principal_filters
from brewtils.errors import AuthorizationRequired

from brewtils.models import Operation, Principal, Permission, Role


@pytest.fixture
def admin_account():
    return Principal(
        id="1", roles=[Role(permissions=[Permission(garden="default", access="ADMIN")])]
    )


@pytest.fixture
def user_account():
    return Principal(
        id="2", roles=[Role(permissions=[Permission(garden="default", access="READ")])]
    )


def mock_operations(user_id="1"):
    return [
        Operation(operation_type="USER_UPDATE", kwargs={"user_id": user_id}),
        Operation(operation_type="USER_UPDATE_ROLE", kwargs={"user_id": user_id}),
        Operation(operation_type="USER_REMOVE_ROLE", kwargs={"user_id": user_id}),
        Operation(operation_type="USER_UPDATE", kwargs={"user_id": user_id}),
    ]


def mock_principal(user_id="1"):
    return [Principal(id=user_id, roles=[])]


def config_get_side_effort(value):
    if value == "garden.name":
        return "default"


def _config_get(monkeypatch):
    mock = Mock(side_effect=config_get_side_effort)

    monkeypatch.setattr(principal_filters.config, "get", mock)

    return mock


class TestPrincipalFilter(object):
    @pytest.mark.parametrize(
        "operation",
        mock_operations(),
    )
    def test_operation_local_admin(self, operation, admin_account, monkeypatch):
        _config_get(monkeypatch)

        assert (
            principal_filters.model_principal_filter(
                obj=operation, current_user=admin_account
            )
            is not None
        )

    @pytest.mark.parametrize(
        "operation",
        mock_operations(),
    )
    def test_operation_local_user_fail(self, operation, user_account, monkeypatch):
        _config_get(monkeypatch)

        assert (
            principal_filters.model_principal_filter(
                obj=operation, raise_error=False, current_user=user_account
            )
            is None
        )

    @pytest.mark.parametrize(
        "operation",
        mock_operations(),
    )
    def test_operation_local_user_fail_raise_error(
        self, operation, user_account, monkeypatch
    ):
        _config_get(monkeypatch)
        with pytest.raises(AuthorizationRequired):
            principal_filters.model_principal_filter(
                obj=operation, raise_error=True, current_user=user_account
            ) is None

    def test_operation_local_user_pass(self, user_account, monkeypatch):
        _config_get(monkeypatch)

        operation = Operation(
            operation_type="USER_UPDATE", kwargs={"user_id": user_account.id}
        )

        assert (
            principal_filters.model_principal_filter(
                obj=operation, current_user=user_account
            )
            is not None
        )

    @pytest.mark.parametrize(
        "principal",
        mock_principal(user_id="2"),
    )
    def test_princiapl_local_admin(self, principal, admin_account, monkeypatch):
        _config_get(monkeypatch)

        assert (
            principal_filters.model_principal_filter(
                obj=principal, current_user=admin_account
            )
            is not None
        )

    @pytest.mark.parametrize(
        "principal",
        mock_principal(user_id="2"),
    )
    def test_princiapl_local_user(self, principal, user_account, monkeypatch):
        _config_get(monkeypatch)

        assert (
            principal_filters.model_principal_filter(
                obj=principal, current_user=user_account
            )
            is not None
        )

    @pytest.mark.parametrize(
        "principal",
        mock_principal(user_id="1"),
    )
    def test_princiapl_local_user_fail(self, principal, user_account, monkeypatch):
        _config_get(monkeypatch)

        assert (
            principal_filters.model_principal_filter(
                obj=principal, raise_error=False, current_user=user_account
            )
            is None
        )

    @pytest.mark.parametrize(
        "principal",
        mock_principal(user_id="1"),
    )
    def test_princiapl_local_user_fail_raise(
        self, principal, user_account, monkeypatch
    ):
        _config_get(monkeypatch)

        with pytest.raises(AuthorizationRequired):
            principal_filters.model_principal_filter(
                obj=principal, raise_error=True, current_user=user_account
            ) is None
