# -*- coding: utf-8 -*-
import pytest
import yaml
from mock import MagicMock, Mock, mock_open, patch
from mongoengine import DoesNotExist, connect

import beer_garden.db.mongo.models
import beer_garden.db.mongo.util
from beer_garden import config
from beer_garden.db.mongo.models import CommandBlackList, Garden, Role
from beer_garden.db.mongo.util import (
    ensure_local_garden,
    ensure_roles,
    is_in_command_black_list,
)
from beer_garden.errors import ConfigurationError


@pytest.fixture
def model_mocks(monkeypatch):
    request_mock = Mock()
    system_mock = Mock()
    role_mock = Mock()
    job_mock = Mock()
    principal_mock = Mock()
    black_list_mock = Mock()
    event_mock = Mock()

    request_mock.__name__ = "Request"
    system_mock.__name__ = "System"
    role_mock.__name__ = "LegacyRole"
    job_mock.__name__ = "Job"
    black_list_mock.__name__ = "CommandBlackList"
    event_mock.__name__ = "event"
    principal_mock.__name__ = "Principal"

    monkeypatch.setattr(beer_garden.db.mongo.models, "Request", request_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "System", system_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "LegacyRole", role_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "Job", job_mock)
    monkeypatch.setattr(
        beer_garden.db.mongo.models, "CommandBlackList", black_list_mock
    )
    monkeypatch.setattr(beer_garden.db.mongo.models, "Principal", principal_mock)

    return {
        "request": request_mock,
        "system": system_mock,
        "role": role_mock,
        "job": job_mock,
        "principal": principal_mock,
        "black_list": black_list_mock,
        "event": event_mock,
    }


class TestEnsureUsers(object):
    def test_already_exists(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.get = Mock()

        beer_garden.db.mongo.util.ensure_users(False)
        principal.assert_not_called()

    def test_others_exist(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=2)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        beer_garden.db.mongo.util.ensure_users(False)
        principal.assert_not_called()

    def test_only_anon_exists(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=1)
        mock_anon = Mock(username="anonymous")
        principal.objects.get = Mock(
            side_effect=[DoesNotExist, [mock_anon], DoesNotExist]
        )

        beer_garden.db.mongo.util.ensure_users(False)
        principal.assert_called_once()

    @patch("passlib.apps.custom_app_context.hash")
    def test_create(self, hash_mock, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        beer_garden.db.mongo.util.ensure_users(False)
        principal.assert_called_once()
        hash_mock.assert_called_with("password")

    @patch("passlib.apps.custom_app_context.hash")
    def test_create_env_password(self, hash_mock, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        with patch.dict("os.environ", {"BG_DEFAULT_ADMIN_PASSWORD": "foo"}):
            beer_garden.db.mongo.util.ensure_users(False)
            principal.assert_called_once()
            hash_mock.assert_called_with("foo")

    def test_guest_login_enabled(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        beer_garden.db.mongo.util.ensure_users(True)
        assert principal.call_count == 2

    def test_remove_anonymous_user(self, model_mocks):
        principal = model_mocks["principal"]
        anon_user = Mock()
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(return_value=anon_user)

        beer_garden.db.mongo.util.ensure_users(False)
        assert anon_user.delete.call_count == 1

    def test_remove_anonymous_user_guest_login_none(self, model_mocks):
        principal = model_mocks["principal"]
        anon_user = Mock()
        principal.objects.get = Mock(return_value=anon_user)

        beer_garden.db.mongo.util.ensure_users(None)
        assert anon_user.delete.call_count == 0


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
        from pymongo.errors import OperationFailure

        # 'normal' return values
        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"index1": {}})
                )
            )

        # ... except for this one
        model_mocks["request"].list_indexes.side_effect = OperationFailure("")

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        assert db_mock["request"].drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db")
    def test_unsuccessful_index_drop(self, get_db_mock, model_mocks):
        from pymongo.errors import OperationFailure

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

            model_mock.ensure_indexes.side_effect = OperationFailure("")

        get_db_mock.side_effect = OperationFailure("")

        for doc in model_mocks.values():
            with pytest.raises(OperationFailure):
                beer_garden.db.mongo.util.check_indexes(doc)

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db", MagicMock())
    def test_unsuccessful_index_rebuild(self, model_mocks):
        from pymongo.errors import OperationFailure

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"index1": {}})
                )
            )

            model_mock.ensure_indexes.side_effect = OperationFailure("")

        for doc in model_mocks.values():
            with pytest.raises(OperationFailure):
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


class TestCommandBlackList(object):
    namespace = "test"
    system = "system_test"
    command = "command_test"

    @pytest.fixture()
    def command_black_list(self):
        black_list = CommandBlackList(
            namespace=self.namespace, system=self.system, command=self.command
        ).save()

        yield black_list
        black_list.delete()

    def test_exists(self, model_mocks, command_black_list):
        model_mocks["event"].payload_type = "Request"
        model_mocks["event"].payload.namespace = self.namespace
        model_mocks["event"].payload.system = self.system
        model_mocks["event"].payload.command = self.command

        assert is_in_command_black_list(model_mocks["event"])

    def test_missing(self, model_mocks):
        model_mocks["event"].payload_type = "Request"
        model_mocks["black_list"].objects.get.return_value = DoesNotExist

        assert not is_in_command_black_list(model_mocks["event"])

    def test_payload_type_not_request(self, model_mocks):
        model_mocks["event"].payload_type = "Garden_create"
        model_mocks["black_list"].objects.get.return_value = DoesNotExist

        assert not is_in_command_black_list(model_mocks["event"])


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

    def config_get_value(self, config_name):
        return "/some/file/path"

    def config_get_none(self, config_name):
        return None

    def test_ensure_roles_creates_roles_defined_in_file(
        self, monkeypatch, role_definition_yaml
    ):
        """ensure_roles should create the roles defined in the auth.role_definition_file
        if specified"""
        monkeypatch.setattr(config, "get", self.config_get_value)

        role_definition_file = config.get("auth.role_definition_file")

        with patch(
            "builtins.open", mock_open(read_data=role_definition_yaml)
        ) as mock_file_read:
            ensure_roles()
            mock_file_read.assert_called_with(role_definition_file, "r")

        assert len(Role.objects.filter(name="testrole1")) == 1

    def test_ensure_roles_creates_no_roles_if_no_file_specified(self, monkeypatch):
        """ensure_roles should not create anything if no auth.role_definition_file
        is specified"""
        monkeypatch.setattr(config, "get", self.config_get_none)
        ensure_roles()

        assert len(Role.objects.filter(name="testrole1")) == 0

    def test_ensure_roles_raises_exception_when_file_not_found(self, monkeypatch):
        """ensure_roles should raise ConfigurationError if the file specified by
        auth.role_definition_file is not found"""
        monkeypatch.setattr(config, "get", self.config_get_value)

        def file_not_found(arg1, arg2):
            raise FileNotFoundError

        with patch("builtins.open", mock_open()) as mock_file_read:
            mock_file_read.side_effect = file_not_found
            with pytest.raises(ConfigurationError):
                ensure_roles()

    def test_ensure_roles_raises_exception_on_schema_errors(
        self, monkeypatch, role_definition_yaml
    ):
        """ensure_roles should raise ConfigurationError if the file specified by
        raises a schema validation error (i.e. does not conform to the expected format)
        """
        from marshmallow.exceptions import ValidationError

        def validation_error(arg):
            raise ValidationError("error")

        monkeypatch.setattr(config, "get", self.config_get_value)
        monkeypatch.setattr(beer_garden.db.mongo.util, "sync_roles", validation_error)

        with patch("builtins.open", mock_open(read_data=role_definition_yaml)):
            with pytest.raises(ConfigurationError):
                ensure_roles()

    def test_ensure_roles_raises_exception_on_permissions_error(
        self, monkeypatch, role_definition_yaml
    ):
        """ensure_roles should raise ConfigurationError if the file specified by
        raises a mongo validation error (e.g. one of the specified permissions is not
        a recognized, valid permission)
        """
        from mongoengine.errors import ValidationError

        def validation_error(arg):
            raise ValidationError("error")

        monkeypatch.setattr(config, "get", self.config_get_value)
        monkeypatch.setattr(beer_garden.db.mongo.util, "sync_roles", validation_error)

        with patch("builtins.open", mock_open(read_data=role_definition_yaml)):
            with pytest.raises(ConfigurationError):
                ensure_roles()
