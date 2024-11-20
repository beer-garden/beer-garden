import json
from pathlib import Path

import pytest
from box import Box
from ldap3 import MOCK_SYNC, Connection, Server
from mock import patch
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.ldap import LdapLoginHandler
from beer_garden.db.mongo.models import Role as DB_Role
from beer_garden.db.mongo.models import User as DB_User
from beer_garden.role import create_role
from beer_garden.user import create_user
from brewtils.models import Role, User

ldap_groups_json = {
    "entries": [
        {
            "attributes": {
                "dc": "example",
                "o": ["Example"],
                "objectClass": ["top", "dcObject", "organization"],
            },
            "dn": "dc=example,dc=com",
            "raw": {
                "dc": ["example"],
                "o": ["Example"],
                "objectClass": ["top", "dcObject", "organization"],
            },
        },
        {
            "attributes": {
                "objectClass": ["organizationalUnit", "top"],
                "ou": ["Users"],
            },
            "dn": "ou=Users,dc=example,dc=com",
            "raw": {"objectClass": ["organizationalUnit", "top"], "ou": ["Users"]},
        },
        {
            "attributes": {
                "objectClass": ["organizationalUnit", "top"],
                "ou": ["Admin"],
                "userPassword": ["{MD5}X03MO1qnZdYdgyfeuILPmQ=="],
            },
            "dn": "ou=Admin,dc=example,dc=com",
            "raw": {
                "objectClass": ["organizationalUnit", "top"],
                "ou": ["Admin"],
                "userPassword": ["{MD5}X03MO1qnZdYdgyfeuILPmQ=="],
            },
        },
        {
            "attributes": {
                "cn": ["plugin_admin"],
                "description": ["plugin admin"],
                "objectClass": ["inetOrgPerson", "top"],
                "sn": ["padmin"],
                "uid": ["plugin_admin"],
                "userPassword": ["{MD5}X03MO1qnZdYdgyfeuILPmQ=="],
            },
            "dn": "uid=plugin_admin,ou=Admin,dc=example,dc=com",
            "raw": {
                "cn": ["plugin_admin"],
                "description": ["plugin admin"],
                "objectClass": ["inetOrgPerson", "top"],
                "sn": ["padmin"],
                "uid": ["plugin_admin"],
                "userPassword": ["{MD5}X03MO1qnZdYdgyfeuILPmQ=="],
            },
        },
        {
            "attributes": {
                "cn": ["John Smith"],
                "description": ["John Smith from Accounting."],
                "objectClass": ["inetOrgPerson", "top"],
                "sn": ["Smith"],
                "uid": ["jsmith1"],
                "userPassword": ["jsmith1"],
            },
            "dn": "uid=jsmith1,ou=Users,dc=example,dc=com",
            "raw": {
                "cn": ["John Smith"],
                "description": ["John Smith from Accounting."],
                "objectClass": ["inetOrgPerson", "top"],
                "sn": ["Smith"],
                "uid": ["jsmith1"],
                "userPassword": ["jsmith1"],
            },
        },
        {
            "attributes": {
                "cn": ["Sally Brown"],
                "description": ["Sally Brown from engineering."],
                "objectClass": ["inetOrgPerson", "top"],
                "sn": ["Brown"],
                "uid": ["sbrown20"],
                "userPassword": ["sbrown20"],
            },
            "dn": "uid=sbrown20,ou=Users,dc=example,dc=com",
            "raw": {
                "cn": ["Sally Brown"],
                "description": ["Sally Brown from engineering."],
                "objectClass": ["inetOrgPerson", "top"],
                "sn": ["Brown"],
                "uid": ["sbrown20"],
                "userPassword": ["sbrown20"],
            },
        },
        {
            "attributes": {
                "objectClass": ["organizationalUnit", "top"],
                "ou": ["Roles"],
            },
            "dn": "ou=Roles,dc=example,dc=com",
            "raw": {"objectClass": ["organizationalUnit", "top"], "ou": ["Roles"]},
        },
        {
            "attributes": {
                "cn": ["garden_admin"],
                "description": ["tagGroup"],
                "member": ["uid=jsmith1,ou=Users,dc=example,dc=com"],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
            "dn": "cn=garden_admin,ou=Roles,dc=example,dc=com",
            "raw": {
                "cn": ["garden_admin"],
                "description": ["tagGroup"],
                "member": ["uid=jsmith1,ou=Users,dc=example,dc=com"],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
        },
        {
            "attributes": {
                "cn": ["plugin_admin"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                    "uid=plugin_admin,ou=Admin,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
            "dn": "cn=plugin_admin,ou=Roles,dc=example,dc=com",
            "raw": {
                "cn": ["plugin_admin"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                    "uid=plugin_admin,ou=Admin,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
        },
        {
            "attributes": {
                "cn": ["operator"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
            "dn": "cn=operator,ou=Roles,dc=example,dc=com",
            "raw": {
                "cn": ["operator"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
        },
        {
            "attributes": {
                "cn": ["read_only"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
            "dn": "cn=read_only,ou=Roles,dc=example,dc=com",
            "raw": {
                "cn": ["read_only"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
        },
        {
            "attributes": {
                "cn": ["manager"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
            "dn": "cn=manager,ou=Roles,dc=example,dc=com",
            "raw": {
                "cn": ["manager"],
                "description": ["tagGroup"],
                "member": [
                    "uid=jsmith1,ou=Users,dc=example,dc=com",
                    "uid=sbrown20,ou=Users,dc=example,dc=com",
                ],
                "objectClass": ["top", "groupOfNames"],
                "ou": ["Roles"],
            },
        },
    ]
}


@pytest.fixture
def ldap_json_group_file(tmpdir):
    config_file = Path(tmpdir, "ldap_entries.json")

    with open(config_file, "w") as f:
        f.write(json.dumps(ldap_groups_json))

    return str(config_file)


@pytest.fixture(autouse=True)
def app_config_ldap_handler(monkeypatch):
    app_config = Box(
        {
            "auth": {
                "enabled": True,
                "authentication_handlers": {
                    "ldap": {
                        "enabled": True,
                        "host": "test-server",
                        "port": 389,
                        "use_ssl": False,
                        "user_prefix": "uid",
                        "user_attributes": "ou=Users",
                        "base_dn": "dc=example,dc=com",
                        "roles_search_base": "dc=example,dc=com",
                        "default_user_roles": ["read_only"],
                    }
                },
            },
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)
    yield app_config


@pytest.fixture
def valid_user():
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=user1,dc=example,dc=com",
        password="user1",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.add_entry(
        "uid=user1,dc=example,dc=com",
        {"userPassword": "user1", "sn": "user1", "revision": 0},
    )

    mock_connection.bind()
    yield mock_connection


@pytest.fixture
def bad_password():
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=user1,dc=example,dc=com",
        password="not_user1",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.add_entry(
        "uid=user1,dc=example,dc=com",
        {"userPassword": "user1", "sn": "user1", "revision": 0},
    )

    mock_connection.bind()
    yield mock_connection


@pytest.fixture
def no_user():
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=baduser,dc=example,dc=com",
        password="not_user1",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.add_entry(
        "uid=user1,dc=example,dc=com",
        {"userPassword": "user1", "sn": "user1", "revision": 0},
    )

    mock_connection.bind()
    yield mock_connection


@pytest.fixture
def ldap_connection(ldap_json_group_file):
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=jsmith1,ou=Users,dc=example,dc=com",
        password="jsmith1",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.entries_from_json(ldap_json_group_file)
    mock_connection.bind()
    yield mock_connection


@pytest.fixture
def ldap_connection2(ldap_json_group_file):
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=sbrown20,ou=Users,dc=example,dc=com",
        password="sbrown20",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.entries_from_json(ldap_json_group_file)
    mock_connection.bind()
    yield mock_connection


@pytest.fixture(autouse=True)
def drop():
    yield
    DB_Role.drop_collection()
    DB_User.drop_collection()


@pytest.fixture
def role0():
    yield create_role(Role(name="invalid", permission="READ_ONLY"))


@pytest.fixture
def role1():
    yield create_role(Role(name="read_only", permission="READ_ONLY"))


@pytest.fixture
def role2():
    yield create_role(Role(name="operator", permission="OPERATOR"))


@pytest.fixture
def role3():
    yield create_role(Role(name="plugin_admin", permission="PLUGIN_ADMIN"))


@pytest.fixture
def role4():
    yield create_role(Role(name="garden_admin", permission="GARDEN_ADMIN"))


class TestLdapLoginHandler:
    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_user_login_bad_default_role(self, mock_connection, valid_user):
        mock_connection.return_value = valid_user
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"user1","password":"user1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "user1"
        assert len(authenticated_user.roles) == 0

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_user_login_default_role(self, mock_connection, valid_user, role1):
        mock_connection.return_value = valid_user
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"user1","password":"user1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "user1"
        assert len(authenticated_user.roles) == 1

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_bad_password(self, mock_connection, bad_password):
        mock_connection.return_value = bad_password
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"user1","password":"not_user1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is None

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_invalid_user(self, mock_connection, no_user):
        mock_connection.return_value = no_user
        handler = LdapLoginHandler()

        request = HTTPServerRequest(
            body=b'{"username":"baduser","password":"not_user1"}'
        )
        authenticated_user = handler.get_user(request)

        assert authenticated_user is None

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_no_added_group(self, mock_connection, ldap_connection):
        mock_connection.return_value = ldap_connection
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"jsmith1","password":"jsmith1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "jsmith1"
        assert len(authenticated_user.roles) == 0

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_default_matches_group(self, mock_connection, ldap_connection, role1):
        mock_connection.return_value = ldap_connection
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"jsmith1","password":"jsmith1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "jsmith1"
        assert len(authenticated_user.roles) == 1

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_added_group(self, mock_connection, ldap_connection, role1, role2):
        mock_connection.return_value = ldap_connection
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"jsmith1","password":"jsmith1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "jsmith1"
        assert len(authenticated_user.roles) == 2

    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_user_groups_replaced(
        self, mock_connection, ldap_connection2, role0, role2, role3, role4
    ):
        user = create_user(User(username="sbrown20", roles=[role0]))
        assert user is not None
        assert user.username == "sbrown20"
        assert len(user.local_roles) == 1

        mock_connection.return_value = ldap_connection2
        handler = LdapLoginHandler()

        request = HTTPServerRequest(
            body=b'{"username":"sbrown20","password":"sbrown20"}'
        )
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "sbrown20"
        assert len(authenticated_user.local_roles) == 2
        for local_role in authenticated_user.local_roles:
            if local_role.name == role2.name or local_role.name == role3.name:
                # Confirm that new roles were added
                assert True
            elif local_role.name == role0.name:
                # Confirm that old role was removed
                assert False
            else:
                # Unknown role added
                assert False
