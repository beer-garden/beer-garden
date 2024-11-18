import pytest
from box import Box
from ldap3 import MOCK_SYNC, Connection, Server
from mock import patch
from tornado.httputil import HTTPServerRequest

from beer_garden import config
from beer_garden.api.http.authentication.login_handlers.ldap import LdapLoginHandler
from beer_garden.db.mongo.models import Role as DB_Role
from beer_garden.role import create_role
from brewtils.models import Role


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
                        "base_dn": "dc=example,dc=com",
                        "roles_search_base": "cn=groups,cn=accounts,dc=example,dc=com",
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


@pytest.fixture(autouse=True)
def drop():
    yield DB_Role.drop_collection()


@pytest.fixture
def role1():
    yield create_role(Role(name="read_only", permission="READ_ONLY"))


class TestLdapLoginHandler:
    @patch(
        "beer_garden.api.http.authentication.login_handlers.ldap.LdapLoginHandler.get_connection"
    )
    def test_user_login(self, mock_connection, valid_user, role1):
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
    def test_no_added_groups(self, mock_connection, valid_user, role1):
        mock_connection.return_value = valid_user
        handler = LdapLoginHandler()

        request = HTTPServerRequest(body=b'{"username":"user1","password":"user1"}')
        authenticated_user = handler.get_user(request)

        assert authenticated_user is not None
        assert authenticated_user.username == "user1"
        assert len(authenticated_user.roles) == 1
