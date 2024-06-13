# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
from box import Box
from brewtils.errors import ModelValidationError
from brewtils.models import Role
from mongoengine import DoesNotExist, connect

from beer_garden import config
from beer_garden.db.mongo.models import Role as DB_Role
from beer_garden.db.mongo.models import User as DB_User
from beer_garden.role import (
    configure_plugin_role,
    configure_superuser_role,
    create_role,
    delete_role,
    get_role,
    rescan,
    update_role,
)
from beer_garden.user import create_user


@pytest.fixture(autouse=True)
def drop():
    DB_Role.drop_collection()
    DB_User.drop_collection()


@pytest.fixture
def role():
    return create_role(Role(name="role", permission="READ_ONLY"))


@pytest.fixture
def roles_file_path(tmpdir):
    roles_file = Path(tmpdir, f"roles.yaml")

    raw_roles = """- name: "garden_admin"
  permission: "GARDEN_ADMIN"

- name: "operator"
  permission: "OPERATOR"

- name: "read_only"
  permission: "READ_ONLY"

- name: "plugin_admin"
  permission: "PLUGIN_ADMIN"
"""

    with open(roles_file, "w") as f:
        f.write(raw_roles)

    return str(roles_file)


@pytest.fixture
def app_config_roles_file(monkeypatch, roles_file_path):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "role_definition_file": roles_file_path,
            }
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def app_config_roles_file_missing(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "role_definition_file": "tmp/roles.yaml",
            }
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def user(role):
    return create_user(username="user", local_roles=[role])


class TestRole:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.parametrize(
        "permission", ["READ_ONLY", "OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"]
    )
    def test_create_valid_permissions(self, permission):

        role = create_role(Role(name="test", permission=permission))
        assert role.id != None

    def test_create_invalid_permission(self):
        with pytest.raises(ModelValidationError):
            create_role(Role(name="test", permission="Bad_Permission"))

    def test_get_role(self, role):
        assert get_role(role_id=role.id) == role
        assert get_role(role_name=role.name) == role

    def test_update_role(self, role):

        role.permission = "OPERATOR"
        update_role(role)
        db_role = get_role(role_id=role.id)
        assert role.permission == db_role.permission

        update_role(role_name=role.name, permission="PLUGIN_ADMIN")
        db_role = get_role(role_name=role.name)
        assert db_role.permission == "PLUGIN_ADMIN"

        update_role(role_id=role.id, permission="GARDEN_ADMIN")
        db_role = get_role(role_id=role.id)
        assert db_role.permission == "GARDEN_ADMIN"

    def test_delete_role(self, role):

        delete_role(role)

        with pytest.raises(DoesNotExist):
            get_role(role_id=role.id)

    def test_create_generated_roles(self):
        configure_superuser_role()
        configure_plugin_role()

        assert get_role(role_name="superuser") is not None
        assert get_role(role_name="plugin") is not None

    def test_rescan_roles(self, app_config_roles_file):
        rescan()

        assert get_role(role_name="garden_admin") is not None
        assert get_role(role_name="plugin_admin") is not None
        assert get_role(role_name="operator") is not None
        assert get_role(role_name="read_only") is not None

    def test_rescan_roles_missing_file(self, app_config_roles_file_missing):
        rescan()

        with pytest.raises(DoesNotExist):
            get_role(role_name="garden_admin")
        with pytest.raises(DoesNotExist):
            get_role(role_name="plugin_admin")
        with pytest.raises(DoesNotExist):
            get_role(role_name="operator")
        with pytest.raises(DoesNotExist):
            get_role(role_name="read_only")

    def test_rescan_roles_overwrite(self, app_config_roles_file):
        garden_admin = create_role(Role(name="garden_admin", permission="READ_ONLY"))
        plugin_admin = create_role(
            Role(name="plugin_admin", scope_systems=["foo", "bar"])
        )

        rescan()

        db_garden_admin = get_role(role_id=garden_admin.id)
        assert db_garden_admin.permission == "GARDEN_ADMIN"

        db_plugin_admin = get_role(role_id=plugin_admin.id)
        assert plugin_admin != db_plugin_admin
        assert len(db_plugin_admin.scope_systems) == 0
