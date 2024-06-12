import pytest
from box import Box
from brewtils.models import AliasUserMap, Role, User
from brewtils.schema_parser import SchemaParser
from marshmallow import ValidationError
from tornado.httputil import HTTPHeaders, HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.trusted_header import (
    TrustedHeaderLoginHandler,
)
from beer_garden.db.mongo.models import Role as DB_Role
from beer_garden.db.mongo.models import User as DB_User
from beer_garden.role import create_role
from beer_garden.user import create_user


@pytest.fixture(autouse=True)
def app_config_trusted_handler(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "authentication_handlers": {
                    "trusted_header": {
                        "enabled": True,
                        "username_header": "bg-username",
                        "user_upstream_roles_header": "bg-user-upstream-roles",
                        "user_local_roles_header": "bg-user-local-roles",
                        "user_alias_user_mapping_header": "bg-user-alias-user-mapping",
                        "create_users": True,
                    }
                },
            },
            "garden": {"name": "somegarden"},
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def app_config_trusted_handler_create_users_false(
    monkeypatch, app_config_trusted_handler
):
    pointer = app_config_trusted_handler.auth.authentication_handlers.trusted_header
    pointer.create_users = False
    monkeypatch.setattr(config, "_CONFIG", app_config_trusted_handler)

    yield app_config_trusted_handler


@pytest.fixture
def app_config_trusted_handler_missing_group_definition_file(
    monkeypatch, app_config_trusted_handler
):
    app_config_trusted_handler.auth.group_definition_file = None
    monkeypatch.setattr(config, "_CONFIG", app_config_trusted_handler)

    yield app_config_trusted_handler


@pytest.fixture(autouse=True)
def drop():
    yield
    DB_User.drop_collection()
    DB_Role.drop_collection()


@pytest.fixture
def user():
    yield create_user(User(username="testuser"))


@pytest.fixture
def role_1():
    yield create_role(Role(name="role1", permission="OPERATOR"))


@pytest.fixture
def role_2():
    yield create_role(Role(name="role2", permission="OPERATOR"))


@pytest.fixture
def alias_user_mapping_1():
    return AliasUserMap(target_garden="child", username="child")


@pytest.fixture
def alias_user_mapping_2():
    return AliasUserMap(target_garden="grandchild", username="grandchild")


@pytest.fixture
def malformed_role():
    return '[{ name": "role1","permission": "Operator","scope_garden": ["child"]}]'


@pytest.fixture
def malformed_user_mappings():
    return '[{"target_gardens":"bad_garden", "username":"user"}]'


def error_logged(caplog, module) -> bool:
    """Verify that the supplied module logged an error"""
    error_logged = False

    for entry in caplog.records:
        if entry.name == module and entry.levelname == "ERROR":
            error_logged = True
            break

    return error_logged


class TestTrustedHeaderLoginHandler:
    def test_get_user_returns_existing_user(self, user, role_1, role_2):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_local_roles_header: f'["{role_1.name}", "{role_2.name}"]',
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == user.username
        assert len(authenticated_user.roles) == 2

    def test_get_user_returns_existing_user_upstream_roles(self, user):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_upstream_roles_header: SchemaParser.serialize_role(
                    [
                        Role(name="newRole1", permission="OPERATOR"),
                        Role(name="newRole2", permission="OPERATOR"),
                    ],
                    to_string=True,
                ),
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == user.username
        assert len(authenticated_user.upstream_roles) == 2

    def test_get_user_creates_new_user(self, role_1, role_2):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: "createNewUser",
                handler.user_local_roles_header: f'["{role_1.name}", "{role_2.name}"]',
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "createNewUser"
        assert len(authenticated_user.roles) == 2

    def test_get_user_handles_create_users_set_to_false(
        self, app_config_trusted_handler_create_users_false, caplog, role_1, role_2
    ):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: "createNewUser",
                handler.user_local_roles_header: f'["{role_1.name}", "{role_2.name}"]',
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is None

    def test_get_user_logs_error_for_invalid_role(self, user, role_1, role_2):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_local_roles_header: f'["{role_1.name}", "role3"]',
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == user.username
        assert len(authenticated_user.roles) == 1

    def test_get_user_returns_existing_user_upstream_roles_malformed(
        self, user, malformed_role
    ):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_upstream_roles_header: malformed_role,
            }
        )
        request = HTTPServerRequest(headers=headers)

        with pytest.raises(ValidationError):
            handler.get_user(request)

    def test_get_user_returns_existing_user_local_roles_malformed(self, user):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_local_roles_header: "[user]",
            }
        )
        request = HTTPServerRequest(headers=headers)

        with pytest.raises(ValidationError):
            handler.get_user(request)

    def test_get_user_returns_existing_user_alias_user_mapping_malformed(self, user):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_alias_user_mapping_header: "[remotemappingbad]",
            }
        )
        request = HTTPServerRequest(headers=headers)

        with pytest.raises(ValidationError):
            handler.get_user(request)
