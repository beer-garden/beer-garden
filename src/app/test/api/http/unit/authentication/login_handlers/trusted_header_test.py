import builtins

import pytest
import yaml
from box import Box
from mock import mock_open
from tornado.httputil import HTTPHeaders, HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.trusted_header import (
    TrustedHeaderLoginHandler,
)
from beer_garden.db.mongo.models import Role, User


@pytest.fixture
def drop():
    yield
    User.drop_collection()


@pytest.fixture(autouse=True)
def app_config_trusted_handler(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "group_definition_file": "/some/fake/path",
                "authentication_handlers": {
                    "trusted_header": {
                        "enabled": True,
                        "username_header": "bg-username",
                        "user_groups_header": "bg-user-groups",
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


@pytest.fixture
def user():
    user = User(username="testuser").save()

    yield user
    user.delete()


@pytest.fixture
def role1():
    role = Role(name="role1").save()

    yield role
    role.delete()


@pytest.fixture
def role2():
    role = Role(name="role2").save()

    yield role
    role.delete()


@pytest.fixture
def group_mapping_yaml(role1, role2):
    group1 = {
        "group": "group1",
        "role_assignments": [
            {
                "role_name": role1.name,
                "domain": {"scope": "Global"},
            }
        ],
    }
    group2 = {
        "group": "group2",
        "role_assignments": [
            {
                "role_name": role1.name,
                "domain": {"scope": "Garden", "identifiers": {"name": "garden1"}},
            },
            {
                "role_name": role2.name,
                "domain": {"scope": "Garden", "identifiers": {"name": "garden1"}},
            },
        ],
    }

    group_mapping = [group1, group2]
    return yaml.dump(group_mapping)


@pytest.fixture
def group_mapping_yaml_missing_role():
    group1 = {
        "group": "group1",
        "role_assignments": [
            {
                "role_name": "notarealrole",
                "domain": {"scope": "Global"},
            }
        ],
    }

    group_mapping = [group1]
    return yaml.dump(group_mapping)


@pytest.fixture
def group_mapping_yaml_malformed():
    group1 = {
        "group": "doesntmatter",
        "role_assignments": [
            {
                "not_role_name": "should_have_been_role_name",
                "domain": {"scope": "Global"},
            }
        ],
    }

    group_mapping = [group1]
    return yaml.dump(group_mapping)


@pytest.fixture
def mock_group_mapping_yaml(monkeypatch, group_mapping_yaml):
    monkeypatch.setattr(builtins, "open", mock_open(read_data=group_mapping_yaml))


@pytest.fixture
def mock_group_mapping_yaml_missing_role(monkeypatch, group_mapping_yaml_missing_role):
    monkeypatch.setattr(
        builtins, "open", mock_open(read_data=group_mapping_yaml_missing_role)
    )


@pytest.fixture
def mock_group_mapping_yaml_malformed(monkeypatch, group_mapping_yaml_malformed):
    monkeypatch.setattr(
        builtins, "open", mock_open(read_data=group_mapping_yaml_malformed)
    )


@pytest.fixture
def mock_group_mapping_yaml_invalid_yaml(monkeypatch):
    monkeypatch.setattr(builtins, "open", mock_open(read_data="{ThisAintYaml"))


def error_logged(caplog, module) -> bool:
    """Verify that the supplied module logged an error"""
    error_logged = False

    for entry in caplog.records:
        if entry.name == module and entry.levelname == "ERROR":
            error_logged = True
            break

    return error_logged


class TestTrustedHeaderLoginHandler:
    def test_init_logs_error_for_malformed_mapping(
        self, caplog, mock_group_mapping_yaml_malformed
    ):
        TrustedHeaderLoginHandler()

        assert error_logged(
            caplog,
            "beer_garden.api.http.authentication.login_handlers.trusted_header",
        )

    def test_init_logs_error_for_invalid_yaml(
        self, caplog, mock_group_mapping_yaml_invalid_yaml
    ):
        TrustedHeaderLoginHandler()

        assert error_logged(
            caplog,
            "beer_garden.api.http.authentication.login_handlers.trusted_header",
        )

    def test_init_logs_error_for_missing_group_definition_file(
        self, monkeypatch, caplog
    ):
        def file_not_found(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(builtins, "open", file_not_found)
        TrustedHeaderLoginHandler()

        assert error_logged(
            caplog,
            "beer_garden.api.http.authentication.login_handlers.trusted_header",
        )

    def test_init_logs_error_for_missing_group_definition_file_config(
        self,
        monkeypatch,
        caplog,
        app_config_trusted_handler_missing_group_definition_file,
    ):
        TrustedHeaderLoginHandler()

        assert error_logged(
            caplog,
            "beer_garden.api.http.authentication.login_handlers.trusted_header",
        )

    def test_get_user_returns_existing_user(self, user, mock_group_mapping_yaml):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_groups_header: "group2",
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == user.username
        assert len(authenticated_user.role_assignments) == 2

    def test_get_user_creates_new_user(self, drop, mock_group_mapping_yaml):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: "newuser",
                handler.user_groups_header: "group2,unmappedgroup",
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "newuser"
        assert len(authenticated_user.role_assignments) == 2

    def test_get_user_handles_create_users_set_to_false(
        self,
        caplog,
        mock_group_mapping_yaml,
        app_config_trusted_handler_create_users_false,
    ):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: "newuser",
                handler.user_groups_header: "group2,unmappedgroup",
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is None

    def test_get_user_logs_error_for_invalid_role(
        self, caplog, user, mock_group_mapping_yaml_missing_role
    ):
        handler = TrustedHeaderLoginHandler()
        headers = HTTPHeaders(
            {
                handler.username_header: user.username,
                handler.user_groups_header: "group1",
            }
        )
        request = HTTPServerRequest(headers=headers)
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == user.username
        assert len(authenticated_user.role_assignments) == 0
        assert error_logged(
            caplog,
            "beer_garden.api.http.authentication.login_handlers.trusted_header",
        )
