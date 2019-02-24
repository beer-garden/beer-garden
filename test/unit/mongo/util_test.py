import pytest
from box import Box
from unittest.mock import patch as patch2
from mock import patch, MagicMock, Mock
from mongoengine import DoesNotExist, NotUniqueError
from pymongo.errors import ServerSelectionTimeoutError

import bg_utils
import bg_utils.mongo.models


class TestMongoUtils(object):
    @pytest.fixture
    def model_mocks(self, monkeypatch):
        request_mock = Mock()
        system_mock = Mock()
        role_mock = Mock()
        job_mock = Mock()
        principal_mock = Mock()
        app_state_mock = Mock()

        request_mock.__name__ = "Request"
        system_mock.__name__ = "System"
        role_mock.__name__ = "Role"
        job_mock.__name__ = "Job"
        principal_mock.__name__ = "Principal"
        app_state_mock.__name__ = "AppState"

        monkeypatch.setattr(bg_utils.mongo.models, "Request", request_mock)
        monkeypatch.setattr(bg_utils.mongo.models, "System", system_mock)
        monkeypatch.setattr(bg_utils.mongo.models, "Role", role_mock)
        monkeypatch.setattr(bg_utils.mongo.models, "Job", job_mock)
        monkeypatch.setattr(bg_utils.mongo.models, "Principal", principal_mock)
        monkeypatch.setattr(bg_utils.mongo.models, "AppState", app_state_mock)

        return {
            "request": request_mock,
            "system": system_mock,
            "role": role_mock,
            "job": job_mock,
            "principal": principal_mock,
            "app_state": app_state_mock,
        }

    @patch("mongoengine.register_connection")
    @patch("mongoengine.connect")
    @patch("bg_utils.mongo.verify_db")
    def test_setup_database_connect(self, verify_mock, connect_mock, register_mock):
        app_config = Box(
            {
                "db": {
                    "name": "db_name",
                    "connection": {
                        "username": "db_username",
                        "password": "db_password",
                        "host": "db_host",
                        "port": "db_port",
                    },
                }
            }
        )
        assert bg_utils.mongo.setup_database(app_config, {}) is True
        connect_mock.assert_called_with(
            alias="aliveness",
            db="db_name",
            username="db_username",
            password="db_password",
            host="db_host",
            port="db_port",
            serverSelectionTimeoutMS=1000,
            socketTimeoutMS=1000,
        )
        register_mock.assert_called_with(
            "default",
            name="db_name",
            username="db_username",
            password="db_password",
            host="db_host",
            port="db_port",
        )
        verify_mock.assert_called_once_with(None, {})

    @patch("mongoengine.connect")
    @patch("bg_utils.mongo.verify_db", Mock())
    def test_setup_database_connect_error(self, connect_mock):
        connect_mock.side_effect = ServerSelectionTimeoutError
        assert bg_utils.mongo.setup_database(MagicMock(), {}) is False

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_check_indexes_same_indexes(self, model_mocks):

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

        [bg_utils.mongo.util._check_indexes(doc) for doc in model_mocks.values()]
        for model_mock in model_mocks.values():
            assert model_mock.ensure_indexes.call_count == 1

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_check_indexes_missing_index(self, model_mocks):

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1", "index2"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

        [bg_utils.mongo.util._check_indexes(doc) for doc in model_mocks.values()]
        for model_mock in model_mocks.values():
            assert model_mock.ensure_indexes.call_count == 1

    @patch("mongoengine.connection.get_db")
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_check_indexes_successful_index_rebuild(self, get_db_mock, model_mocks):
        from pymongo.errors import OperationFailure

        # 'normal' return values
        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

        # ... except for this one
        model_mocks["request"].list_indexes.side_effect = OperationFailure("")

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [bg_utils.mongo.util._check_indexes(doc) for doc in model_mocks.values()]
        assert db_mock["request"].drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db")
    def test_check_indexes_unsuccessful_index_drop(self, get_db_mock, model_mocks):
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
                bg_utils.mongo.util._check_indexes(doc)

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db", MagicMock())
    def test_check_indexes_unsuccessful_index_rebuild(self, model_mocks):
        from pymongo.errors import OperationFailure

        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

            model_mock.ensure_indexes.side_effect = OperationFailure("")

        for doc in model_mocks.values():
            with pytest.raises(OperationFailure):
                bg_utils.mongo.util._check_indexes(doc)

    @patch("mongoengine.connection.get_db")
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_check_indexes_old_request_index(self, get_db_mock, model_mocks):
        # 'normal' return values
        for model_mock in model_mocks.values():
            model_mock.list_indexes = Mock(return_value=["index1"])
            model_mock._get_collection = Mock(
                return_value=Mock(index_information=Mock(return_value={"index1": {}}))
            )

        # ... except for this one
        model_mocks[
            "request"
        ]._get_collection.return_value.index_information.return_value = {
            "index1": {},
            "parent_instance_index": {},
        }

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [bg_utils.mongo.util._check_indexes(doc) for doc in model_mocks.values()]
        assert db_mock["request"].drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True

    def test_create_role_exists(self, model_mocks):
        role = Mock()
        model_mocks["role"].objects.get.return_value = role

        bg_utils.mongo.util._create_role(role)
        assert role.save.called is False

    def test_create_role_missing(self, model_mocks):
        role = Mock()
        model_mocks["role"].objects.get.side_effect = DoesNotExist

        bg_utils.mongo.util._create_role(role)
        assert role.save.called is True

    def test_ensure_roles(self, model_mocks):
        bg_utils.mongo.util._ensure_roles()
        assert 3 == model_mocks["role"].objects.get.call_count

    def test_ensure_roles_new_install(self, model_mocks):
        model_mocks["role"].objects.count.return_value = 0
        model_mocks["role"].objects.get.side_effect = DoesNotExist

        bg_utils.mongo.util._ensure_roles()
        assert 5 == model_mocks["role"].objects.get.call_count

    def test_ensure_roles_new_install_race_convenience(self, model_mocks):
        """Race condition where another process created a convenience role"""
        model_mocks["role"].objects.count.return_value = 0
        model_mocks["role"].objects.get.side_effect = [NotUniqueError] + [
            DoesNotExist for _ in range(4)
        ]

        bg_utils.mongo.util._ensure_roles()
        assert 5 == model_mocks["role"].objects.get.call_count

    def test_ensure_roles_new_install_race_mandatory(self, model_mocks):
        """Race condition where another process created a mandatory role"""
        model_mocks["role"].objects.count.return_value = 0
        model_mocks["role"].objects.get.side_effect = [
            DoesNotExist for _ in range(4)
        ] + [NotUniqueError]

        with pytest.raises(NotUniqueError):
            bg_utils.mongo.util._ensure_roles()

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    def test_ensure_users_already_exists(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.get = Mock()
        bg_utils.mongo.util.verify_db(False, {})
        principal.assert_not_called()

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    def test_ensure_users_others_exist(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=2)
        principal.objects.get = Mock(side_effect=DoesNotExist)
        bg_utils.mongo.util.verify_db(False, {})
        principal.assert_not_called()

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    def test_ensure_users_only_anon_exists(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=1)
        mock_anon = Mock(username="anonymous")
        principal.objects.get = Mock(
            side_effect=[DoesNotExist, [mock_anon], DoesNotExist]
        )
        bg_utils.mongo.util.verify_db(False, {})
        principal.assert_called_once()

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    @patch("passlib.apps.custom_app_context.hash")
    def test_ensure_users_create(self, hash_mock, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        bg_utils.mongo.util.verify_db(False, {})
        principal.assert_called_once()
        hash_mock.assert_called_with("password")

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    @patch("passlib.apps.custom_app_context.hash")
    def test_ensure_users_create_env_password(self, hash_mock, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        with patch2.dict("os.environ", {"BG_DEFAULT_ADMIN_PASSWORD": "foo"}):
            bg_utils.mongo.util.verify_db(False, {})
            principal.assert_called_once()
            hash_mock.assert_called_with("foo")

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    def test_ensure_users_guest_login_enabled(self, model_mocks):
        principal = model_mocks["principal"]
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(side_effect=DoesNotExist)

        bg_utils.mongo.util.verify_db(True, {})
        assert principal.call_count == 2

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    def test_remove_anonymous_user(self, model_mocks):
        principal = model_mocks["principal"]
        anon_user = Mock()
        principal.objects.count = Mock(return_value=0)
        principal.objects.get = Mock(return_value=anon_user)

        bg_utils.mongo.util.verify_db(False, {})
        assert anon_user.delete.call_count == 1

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_application_state", Mock())
    def test_remove_anonymous_user_guest_login_none(self, model_mocks):
        principal = model_mocks["principal"]
        anon_user = Mock()
        principal.objects.get = Mock(return_value=anon_user)

        bg_utils.mongo.util.verify_db(None, {})
        assert anon_user.delete.call_count == 0

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_users", Mock())
    def test_ensure_application_state_first_time(self, model_mocks):
        app_state = model_mocks["app_state"]
        app_state.objects.first = Mock(return_value=None)

        bg_utils.mongo.util.verify_db(False, {"foo": "bar"})
        app_state.assert_called_with(
            versions={"foo": "bar"}, auth={"initialized": False}
        )

    @patch("bg_utils.mongo.util._check_indexes", Mock())
    @patch("bg_utils.mongo.util._ensure_roles", Mock())
    @patch("bg_utils.mongo.util._ensure_users", Mock())
    def test_ensure_application_state_update(self, model_mocks):
        app_state = model_mocks["app_state"]
        fake_model = Mock(versions={"foo": "bar"})
        app_state.objects.first = Mock(return_value=fake_model)
        fake_model.save = Mock()

        bg_utils.mongo.util.verify_db(False, {"foo": "bar2", "bat": "baz"})
        assert fake_model.versions == {"foo": "bar2", "bat": "baz"}
        assert fake_model.save.called
