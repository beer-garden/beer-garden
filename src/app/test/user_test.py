# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from box import Box
from brewtils.models import (
    AliasUserMap,
    Command,
    Garden,
    Instance,
    Role,
    System,
    User,
    UserToken,
)
from brewtils.schema_parser import SchemaParser
from mock import Mock
from mongoengine import DoesNotExist

import beer_garden
from beer_garden import config
from beer_garden.db.mongo.models import Role as DB_Role
from beer_garden.db.mongo.models import User as DB_User
from beer_garden.db.mongo.models import UserToken as DB_UserToken
from beer_garden.errors import ConfigurationError, InvalidPasswordException
from beer_garden.role import create_role, get_role
from beer_garden.role import rescan as role_rescan
from beer_garden.user import (
    create_token,
    create_user,
    delete_token,
    delete_user,
    flatten_user_role,
    generate_alias_user_mappings,
    generate_downstream_user,
    get_token,
    get_user,
    get_users,
    has_token,
    rescan,
    revoke_tokens,
    set_password,
    update_user,
    upstream_role_match_garden,
    upstream_user_sync,
    validated_token_ttl,
    verify_password,
)


@pytest.fixture(autouse=True)
def drop():
    yield
    DB_Role.drop_collection()
    DB_User.drop_collection()
    DB_UserToken.drop_collection()


@pytest.fixture
def user_file_path(tmpdir):
    user_file = Path(tmpdir, f"users.yaml")

    raw_users = """- username: "user1"
  roles:
    - "operator"

- username: "user2"
  roles:
    - "garden_admin"

- username: "user3"
  roles:
    - "read_only"

- username: "user4"
  roles:
    - "plugin_admin"
"""

    with open(user_file, "w") as f:
        f.write(raw_users)

    return str(user_file)


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
def local_role():
    return create_role(Role(name="local_role", permission="READ_ONLY"))


@pytest.fixture
def upstream_role():
    return Role(name="upstream_role", permission="READ_ONLY")


@pytest.fixture
def user(local_role, upstream_role):
    return create_user(
        User(username="user", local_roles=[local_role], upstream_roles=[upstream_role])
    )


@pytest.fixture
def user_token(user):
    return create_token(
        UserToken(
            uuid=uuid4(),
            username=user.username,
            expires_at=datetime.utcnow() + timedelta(hours=12),
        )
    )


@pytest.fixture
def app_config_users_file(monkeypatch, roles_file_path, user_file_path):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "role_definition_file": roles_file_path,
                "user_definition_file": user_file_path,
            }
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def app_config_valid_ttl(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "token_access_ttl": {
                    "garden_admin": 15,
                    "operator": 15,
                    "plugin_admin": 15,
                    "read_only": 15,
                },
                "token_refresh_ttl": {
                    "garden_admin": 720,
                    "operator": 720,
                    "plugin_admin": 720,
                    "read_only": 720,
                },
            }
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def roles_loaded(app_config_users_file):
    role_rescan()


@pytest.fixture
def app_config_invalid_ttl(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "token_access_ttl": {
                    "garden_admin": 15,
                    "operator": 15,
                    "plugin_admin": 15,
                    "read_only": 1500,
                },
                "token_refresh_ttl": {
                    "garden_admin": 720,
                    "operator": 720,
                    "plugin_admin": 720,
                    "read_only": 720,
                },
            }
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


class TestUserToken:
    def test_get_user_token(self, user_token):
        assert get_token(user_token.uuid) is not None

    def test_delete_user_token(self, user_token):
        delete_token(user_token)

        with pytest.raises(DoesNotExist):
            get_token(user_token.uuid)

    def test_has_token(self, user_token):
        assert has_token(user_token.username)
        assert not has_token("NO_MATCH")

    def test_revoke_tokens_by_username(self, user_token):
        revoke_tokens(username=user_token.username)
        assert not has_token(user_token.username)

    def test_revoke_tokens_by_user(self, user_token, user):
        revoke_tokens(user=user)
        assert not has_token(user.username)

    def test_validated_token_ttl(self, app_config_valid_ttl):
        validated_token_ttl()
        assert True

    def test_validated_token_ttl(self, app_config_invalid_ttl):
        with pytest.raises(ConfigurationError):
            validated_token_ttl()


class TestUser:
    def test_create_user(self, local_role, upstream_role):
        user_created = create_user(
            User(
                username="created",
                local_roles=[local_role],
                upstream_roles=[upstream_role],
            )
        )

        assert user_created.id is not None

    def test_get_user(self, user):
        db_user = get_user(username=user.username)
        assert db_user == user

    def test_get_user_skip_roles(self, user):
        db_user = get_user(username=user.username, include_roles=False)
        assert len(db_user.roles) == 1
        assert len(db_user.local_roles) == 0

    def test_get_users(self, user):
        assert len(get_users()) == 1

    def test_delete_user(self, user):
        delete_user(user=user)
        with pytest.raises(DoesNotExist):
            get_user(username=user.username)

    def test_update_user(self, user, monkeypatch, app_config_users_file):
        revoke_mock = Mock()

        monkeypatch.setattr(beer_garden.user, "revoke_tokens", revoke_mock)

        role_rescan()
        updated_user = update_user(user=user, roles=["read_only", "plugin_admin"])

        assert len(updated_user.roles) == 2
        revoke_mock.assert_called_once()

    def test_update_user_local_roles(self, user, monkeypatch, app_config_users_file):
        revoke_mock = Mock()

        monkeypatch.setattr(beer_garden.user, "revoke_tokens", revoke_mock)
        role_rescan()

        updated_user = update_user(
            user=user, local_roles=[get_role("read_only"), get_role("plugin_admin")]
        )

        assert len(updated_user.roles) == 2
        revoke_mock.assert_called_once()

    def test_update_user_remote(self, user):
        user.is_remote = True
        user = update_user(user=user)

        user.upstream_roles = [
            Role(name="test1", permission="READ_ONLY"),
            Role(name="test2", permission="READ_ONLY"),
        ]

        update_user(user=user)

        db_user = get_user(username=user.username)

        assert len(user.upstream_roles) == 2

    def test_update_user_change_invalid_password(self, user):
        password = "test"
        set_password(user, password=password)
        update_user(user=user, current_password="bad", password="new")

    def test_update_user_change_valid_password(self, user):
        password = "test"
        set_password(user, password=password)
        update_user(user=user, current_password=password, password="new")

    def test_set_password(self, user):
        password = "test"
        set_password(user, password=password)

        assert user.password != password

    def test_verify_password(self, user):
        password = "test"
        set_password(user, password=password)

        assert user.password != password

        assert verify_password(user, password)

    def test_verify_invalid_password(self, user):
        password = "test"
        set_password(user, password=password)

        assert not verify_password(user, "invalid")

    def test_rescan_users(self, app_config_users_file):
        role_rescan()
        rescan()

        user1 = get_user(username="user1")
        for role in user1.local_roles:
            assert role.name == "operator"

        user2 = get_user(username="user2")
        for role in user2.local_roles:
            assert role.name == "garden_admin"

        user3 = get_user(username="user3")
        for role in user3.local_roles:
            assert role.name == "read_only"

        user4 = get_user(username="user4")
        for role in user4.local_roles:
            assert role.name == "plugin_admin"


class TestUserForwarding:
    def test_flatten_user_role(self):
        role = Role(
            name="test",
            scope_gardens=["A", "B"],
            scope_systems=["foo", "bar"],
            scope_commands=["command1", "command2"],
        )
        flatten_roles = []
        flatten_user_role(role, flatten_roles)

        assert len(flatten_roles) == 8
        valid_roles = [
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["foo"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["foo"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["bar"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["bar"],
                    scope_commands=["command1"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["foo"],
                    scope_commands=["command2"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["foo"],
                    scope_commands=["command2"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["A"],
                    scope_systems=["bar"],
                    scope_commands=["command2"],
                )
            ),
            SchemaParser.serialize_role(
                Role(
                    name="test",
                    scope_gardens=["B"],
                    scope_systems=["bar"],
                    scope_commands=["command2"],
                )
            ),
        ]

        for flatten_role in flatten_roles:
            assert SchemaParser.serialize_role(flatten_role) in valid_roles

    def test_flatten_user_role_no_change(self):
        role = Role(
            name="test",
            scope_gardens=["A"],
            scope_systems=["foo"],
            scope_commands=["command1"],
        )
        flatten_roles = flatten_user_role(role, [])

        assert len(flatten_roles) == 1
        assert SchemaParser.serialize_role(
            flatten_roles[0]
        ) == SchemaParser.serialize_role(
            Role(
                name="test",
                scope_gardens=["A"],
                scope_systems=["foo"],
                scope_commands=["command1"],
            )
        )

    def test_upstream_role_match_garden(self):
        role_1 = Role(
            name="test_1",
            scope_gardens=["A"],
            scope_systems=["foo"],
            scope_commands=["command1"],
        )
        role_2 = Role(name="test_2", scope_systems=["bar"])
        role_3 = Role(name="test_3")
        role_4 = Role(name="test_3", scope_versions=["1"])
        role_5 = Role(name="test_3", scope_instances=["beta"])

        garden_1 = Garden(
            name="A",
            systems=[
                System(
                    name="foo",
                    instances=[Instance(name="alpha")],
                    version="1",
                    commands=[Command(name="command1")],
                )
            ],
        )
        garden_2 = Garden(
            name="B",
            systems=[
                System(
                    name="bar",
                    instances=[Instance(name="beta")],
                    version="1",
                    commands=[Command(name="command2")],
                )
            ],
        )
        garden_3 = Garden(name="C")

        assert upstream_role_match_garden(role_1, garden_1)
        assert not upstream_role_match_garden(role_1, garden_2)
        assert not upstream_role_match_garden(role_1, garden_3)

        assert not upstream_role_match_garden(role_2, garden_1)
        assert upstream_role_match_garden(role_2, garden_2)
        assert upstream_role_match_garden(role_2, garden_3)

        assert upstream_role_match_garden(role_3, garden_1)
        assert upstream_role_match_garden(role_3, garden_2)
        assert upstream_role_match_garden(role_3, garden_3)

        assert upstream_role_match_garden(role_4, garden_1)
        assert upstream_role_match_garden(role_4, garden_2)
        assert upstream_role_match_garden(role_4, garden_3)

        assert not upstream_role_match_garden(role_5, garden_1)
        assert upstream_role_match_garden(role_5, garden_2)
        assert upstream_role_match_garden(role_5, garden_3)

    def test_generate_downstream_user(self):
        garden_1 = Garden(
            name="A",
            systems=[
                System(
                    name="foo",
                    instances=[Instance(name="alpha")],
                    version="1",
                    commands=[Command(name="command1")],
                )
            ],
        )
        garden_2 = Garden(
            name="B",
            children=[garden_1],
            systems=[
                System(
                    name="bar",
                    instances=[Instance(name="beta")],
                    version="1",
                    commands=[Command(name="command2")],
                )
            ],
        )
        garden_3 = Garden(name="C", shared_users=True)

        local_user = User(
            username="test",
            local_roles=[
                Role(
                    name="test_1",
                    scope_gardens=["A"],
                    scope_systems=["foo"],
                    scope_commands=["command1"],
                ),
                Role(
                    name="test_2",
                    scope_systems=["bar"],
                    scope_commands=["command1", "command2"],
                ),
            ],
            alias_user_mapping=[
                AliasUserMap(target_garden="A", username="USER1"),
                AliasUserMap(target_garden="B", username="USER2"),
            ],
        )

        downstream_user_1 = generate_downstream_user(garden_1, local_user)
        assert downstream_user_1.username == "USER1"
        assert len(downstream_user_1.local_roles) == 0
        assert len(downstream_user_1.upstream_roles) == 1
        assert len(downstream_user_1.alias_user_mapping) == 0

        downstream_user_2 = generate_downstream_user(garden_2, local_user)
        assert downstream_user_2.username == "USER2"
        assert len(downstream_user_2.local_roles) == 0
        assert len(downstream_user_2.upstream_roles) == 2
        assert len(downstream_user_2.alias_user_mapping) == 1
        assert downstream_user_2.alias_user_mapping[0].target_garden == "A"
        assert downstream_user_2.alias_user_mapping[0].username == "USER1"

        downstream_user_3 = generate_downstream_user(garden_3, local_user)
        assert downstream_user_3.username == local_user.username
        assert len(downstream_user_3.local_roles) == 0
        assert len(downstream_user_3.upstream_roles) == len(local_user.local_roles)
        assert len(downstream_user_3.alias_user_mapping) == len(
            local_user.alias_user_mapping
        )

    def test_generate_alias_user_mappings(self, user):
        alias_user_mapping = [
            AliasUserMap(target_garden="a", username="test"),
            AliasUserMap(target_garden="b", username="test"),
            AliasUserMap(target_garden="c", username="test"),
        ]

        one_match_garden = Garden(name="target", children=[Garden(name="a")])
        two_match_garden = Garden(
            name="target", children=[Garden(name="b", children=[Garden(name="c")])]
        )
        three_match_garden = Garden(
            name="target",
            children=[
                Garden(
                    name="c", children=[Garden(name="b", children=[Garden(name="a")])]
                )
            ],
        )

        one_match_user = User(username="username")
        two_match_user = User(username="username")
        three_match_user = User(username="username")

        generate_alias_user_mappings(
            one_match_user, one_match_garden, alias_user_mapping
        )
        generate_alias_user_mappings(
            two_match_user, two_match_garden, alias_user_mapping
        )
        generate_alias_user_mappings(
            three_match_user, three_match_garden, alias_user_mapping
        )

        assert len(one_match_user.alias_user_mapping) == 1
        assert len(two_match_user.alias_user_mapping) == 2
        assert len(three_match_user.alias_user_mapping) == 3


class TestUpstreamSync:
    def test_upstream_user_sync_create(self):
        new_user = User(
            username="test_user",
            is_remote=True,
            upstream_roles=[Role(name="upstream", permission="READ_ONLY")],
        )
        upstream_user_sync(new_user)

        db_user = get_user(username=new_user.username)

        assert len(db_user.upstream_roles) == 1
        assert db_user.is_remote

    def test_upstream_user_sync_local(self, user):
        new_user = User(
            username=user.username,
            is_remote=True,
            upstream_roles=[Role(name="upstream", permission="READ_ONLY")],
        )
        upstream_user_sync(new_user)

        db_user = get_user(username=new_user.username)

        assert len(db_user.upstream_roles) == 1
        assert not db_user.is_remote

    def test_upstream_user_sync_override(self, roles_loaded):
        username = "test_user"
        user.is_remote = True
        create_user(User(username=username, is_remote=True, roles=["plugin_admin"]))

        upstream_user_sync(
            User(
                username=username,
                is_remote=True,
                upstream_roles=[Role(name="upstream", permission="READ_ONLY")],
            )
        )

        db_user = get_user(username=username)

        assert len(db_user.upstream_roles) == 1
        assert len(db_user.roles) == 0
        assert db_user.is_remote
