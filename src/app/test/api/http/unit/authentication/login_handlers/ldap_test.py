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
def ldap_connection():
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=jsmith1,ou=Users,dc=example,dc=com",
        password="jsmith1",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.entries_from_json("ldap_entries.json")
    mock_connection.bind()
    yield mock_connection


@pytest.fixture
def ldap_connection2():
    server = Server(host="test-server", port=389, use_ssl=False)
    mock_connection = Connection(
        server,
        user="uid=sbrown20,ou=Users,dc=example,dc=com",
        password="sbrown20",
        client_strategy=MOCK_SYNC,
    )

    mock_connection.strategy.entries_from_json("ldap_entries.json")
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

        authenticated_user = handler.get_user(request)
