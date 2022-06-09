# -*- coding: utf-8 -*-
import pytest
import yaml
from mock import MagicMock, Mock, mock_open, patch
from mongoengine import DoesNotExist, connect

import beer_garden.db.mongo.models
import beer_garden.db.mongo.util
from beer_garden import config
from beer_garden.api.authorization import Permissions
from beer_garden.db.mongo.models import Garden, Role, User
from beer_garden.db.mongo.util import ensure_local_garden, ensure_roles, ensure_users
from beer_garden.db.mongo.util import (
    PLUGIN_ROLE_PERMISSIONS,
    ensure_local_garden,
    ensure_roles,
    ensure_users,
)
from beer_garden.errors import ConfigurationError, IndexOperationError


@pytest.fixture
def model_mocks(monkeypatch):
    request_mock = Mock()
    system_mock = Mock()
    role_mock = Mock()
    job_mock = Mock()

    request_mock.__name__ = "Request"
    system_mock.__name__ = "System"
    role_mock.__name__ = "LegacyRole"
    job_mock.__name__ = "Job"

    monkeypatch.setattr(beer_garden.db.mongo.models, "Request", request_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "System", system_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "LegacyRole", role_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "Job", job_mock)

    return {
        "request": request_mock,
        "system": system_mock,
        "role": role_mock,
        "job": job_mock,
    }


@pytest.fixture
def config_mock_value(monkeypatch):
    def config_get_value(config_name):
        return "somevalue"

    monkeypatch.setattr(config, "get", config_get_value)


@pytest.fixture
def config_mock_none(monkeypatch):
    def config_get_value(config_name):
        return None

    monkeypatch.setattr(config, "get", config_get_value)


class TestEnsureUsers(object):
    @pytest.fixture
    def existing_user(self):
        user = User(username="someuser").save()

        yield user
        user.delete()

    @pytest.fixture
    def roles(self):
        ensure_roles()
        yield
        Role.drop_collection()

    def test_admin_created_if_no_users_exist(
        self, monkeypatch, roles, config_mock_value
    ):
        monkeypatch.setattr(User, "save", Mock())
        ensure_users()

        assert User.save.call_count == 2  # Default Admin, Plugin

    def test_admin_not_created_if_users_exist(
        self, monkeypatch, existing_user, roles, config_mock_value
    ):
        monkeypatch.setattr(User, "save", Mock())
        ensure_users()

        assert User.save.called is False


class TestCheckIndexes(object):
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_same_indexes(self, model_mocks):

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        for model_mock in model_mocks.values():
            assert model_mock.ensure_indexes.call_count == 1

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_missing_index(self, model_mocks):

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1", "index2"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        for model_mock in model_mocks.values():
            assert model_mock.ensure_indexes.call_count == 1

    @patch("mongoengine.connection.get_db")
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_successful_index_rebuild(self, get_db_mock, model_mocks):


        # 'normal' return values
        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"index1": {}})
                )
            )

        # ... except for this one
        model_mocks["request"].list_indexes.side_effect = IndexOperationError("")

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        assert db_mock["request"].drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db")
    def test_unsuccessful_index_drop(self, get_db_mock, model_mocks):

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

            model_mock.ensure_indexes.side_effect = IndexOperationError("")

        get_db_mock.side_effect = IndexOperationError("")

        for doc in model_mocks.values():
            with pytest.raises(IndexOperationError):
                beer_garden.db.mongo.util.check_indexes(doc)

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db", MagicMock())
    def test_unsuccessful_index_rebuild(self, model_mocks):

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"index1": {}})
                )
            )

            model_mock.ensure_indexes.side_effect = IndexOperationError("")

        for doc in model_mocks.values():
            with pytest.raises(IndexOperationError):
                beer_garden.db.mongo.util.check_indexes(doc)

    @patch("mongoengine.connection.get_db")
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_old_request_index(self, get_db_mock, model_mocks, monkeypatch):
        # 'normal' return values
        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"index1": {}})
                )
            )

        # ... except for this one
        model_mocks[
            "request"
        ]._get_collection.return_value.index_information.return_value = {
            "index1": {},
            "parent_instance_index": {},
        }

        # Mock out request model update methods
        update_parent_field_type_mock = Mock()
        update_has_parent_mock = Mock()
        monkeypatch.setattr(
            beer_garden.db.mongo.util,
            "_update_request_parent_field_type",
            update_parent_field_type_mock,
        )
        monkeypatch.setattr(
            beer_garden.db.mongo.util,
            "_update_request_has_parent_model",
            update_has_parent_mock,
        )

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        assert db_mock["request"].drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True
        assert update_parent_field_type_mock.called is True
        assert update_has_parent_mock.called is True


class TestCreateLegacyRole(object):
    def test_exists(self, model_mocks):
        role = Mock()
        model_mocks["role"].objects.get.return_value = role

        beer_garden.db.mongo.util._create_role(role)
        assert role.save.called is False

    def test_missing(self, model_mocks):
        role = Mock()
        model_mocks["role"].objects.get.side_effect = DoesNotExist

        beer_garden.db.mongo.util._create_role(role)
        assert role.save.called is True


class TestEnsureLocalGarden:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def teardown_method(self):
        beer_garden.db.mongo.models.Garden.drop_collection()

    def config_get(self, config_name):
        return "testgarden"

    def test_ensure_local_garden_creates_new_garden_from_config(self, monkeypatch):
        """ensure_local_garden should create a Garden entry in the database with
        name derived from the "garden.name" config setting and a connection type of
        LOCAL"""
        monkeypatch.setattr(config, "get", self.config_get)

        ensure_local_garden()
        garden = Garden.objects.get(connection_type="LOCAL")

        assert garden.name == config.get("garden.name")

    def test_ensure_local_garden_updates_garden_from_config(self, monkeypatch):
        """ensure_local_garden should update the name of an existing Garden entry in the
        database with a connection type of LOCAL"""
        monkeypatch.setattr(config, "get", self.config_get)

        Garden(name="thisshouldchange", connection_type="LOCAL").save()
        ensure_local_garden()
        garden = Garden.objects.get(connection_type="LOCAL")

        assert garden.name == config.get("garden.name")


class TestEnsureRoles:
    @pytest.fixture
    def role_definition_yaml(self):
        role_list = [{"name": "testrole1", "permissions": ["garden:read"]}]
        yield yaml.dump(role_list)

    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def teardown_method(self):
        beer_garden.db.mongo.models.Role.drop_collection()

    def test_ensure_roles_creates_roles_defined_in_file(
        self, role_definition_yaml, config_mock_value
    ):
        """ensure_roles should create the roles defined in the auth.role_definition_file
        if specified"""
        role_definition_file = config.get("auth.role_definition_file")

        with patch(
            "builtins.open", mock_open(read_data=role_definition_yaml)
        ) as mock_file_read:
            ensure_roles()
            mock_file_read.assert_called_with(role_definition_file, "r")

        assert len(Role.objects.filter(name="testrole1")) == 1

    def test_ensure_roles_creates_no_roles_if_no_file_specified(self, config_mock_none):
        """ensure_roles should not create anything if no auth.role_definition_file
        is specified"""
        ensure_roles()

        assert len(Role.objects.filter(name="testrole1")) == 0

    def test_ensure_roles_raises_exception_when_file_not_found(self, config_mock_value):
        """ensure_roles should raise ConfigurationError if the file specified by
        auth.role_definition_file is not found"""

        def file_not_found(arg1, arg2):
            raise FileNotFoundError

        with patch("builtins.open", mock_open()) as mock_file_read:
            mock_file_read.side_effect = file_not_found
            with pytest.raises(ConfigurationError):
                ensure_roles()

    def test_ensure_roles_raises_exception_on_schema_errors(
        self, monkeypatch, role_definition_yaml, config_mock_value
    ):
        """ensure_roles should raise ConfigurationError if the file specified by
        raises a schema validation error (i.e. does not conform to the expected format)
        """
        from marshmallow.exceptions import ValidationError

        def validation_error(arg):
            raise ValidationError("error")

        monkeypatch.setattr(beer_garden.db.mongo.util, "sync_roles", validation_error)

        with patch("builtins.open", mock_open(read_data=role_definition_yaml)):
            with pytest.raises(ConfigurationError):
                ensure_roles()

    def test_ensure_roles_raises_exception_on_permissions_error(
        self, monkeypatch, role_definition_yaml, config_mock_value
    ):
        """ensure_roles should raise ConfigurationError if the file specified by
        raises a mongo validation error (e.g. one of the specified permissions is not
        a recognized, valid permission)
        """
        from mongoengine.errors import ValidationError

        def validation_error(arg):
            raise ValidationError("error")

        monkeypatch.setattr(beer_garden.db.mongo.util, "sync_roles", validation_error)

        with patch("builtins.open", mock_open(read_data=role_definition_yaml)):
            with pytest.raises(ConfigurationError):
                ensure_roles()

    def test_ensure_roles_creates_superuser_role_if_none_exists(self, monkeypatch):
        """A superuser role with all permissions should be created if none exists"""
        monkeypatch.setattr(
            beer_garden.db.mongo.util, "_sync_roles_from_role_definition_file", Mock()
        )

        assert len(Role.objects.filter(name="superuser")) == 0
        ensure_roles()
        superuser = Role.objects.get(name="superuser")

        assert len(superuser.permissions) == len(Permissions)

    def test_ensure_roles_creates_bg_plugin_role_if_none_exists(self, monkeypatch):
        """A plugin role with all permissions should be created if none exists"""
        monkeypatch.setattr(
            beer_garden.db.mongo.util, "_sync_roles_from_role_definition_file", Mock()
        )

        assert len(Role.objects.filter(name="plugin")) == 0
        ensure_roles()
        plugin_role = Role.objects.get(name="plugin")

        assert plugin_role.permissions == PLUGIN_ROLE_PERMISSIONS
