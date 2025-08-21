# -*- coding: utf-8 -*-
import copy
from datetime import datetime

import gridfs
import pytest
from bson.dbref import DBRef
from mock import MagicMock, Mock, patch
from mongoengine import connect
from mongoengine.connection import get_db
from mongoengine.errors import FieldDoesNotExist

import beer_garden.db.mongo.models
import beer_garden.db.mongo.util
from beer_garden import config
from beer_garden.db.mongo.models import Garden
from beer_garden.db.mongo.util import (  # ensure_roles,; ensure_users,
    contains_fields,
    ensure_local_garden,
    ensure_v3_29_model_migration,
    ensure_v3_30_model_migration,
)
from beer_garden.errors import IndexOperationError
from mongomock.gridfs import enable_gridfs_integration

enable_gridfs_integration()


@pytest.fixture
def model_mocks(monkeypatch):
    request_mock = Mock(
        objects=Mock(count=Mock(return_value=1), first=Mock(return_value=[{}]))
    )
    system_mock = Mock(
        objects=Mock(count=Mock(return_value=1), first=Mock(return_value=[{}]))
    )
    job_mock = Mock(
        objects=Mock(count=Mock(return_value=1), first=Mock(return_value=[{}]))
    )

    request_mock.__name__ = "Request"
    system_mock.__name__ = "System"
    job_mock.__name__ = "Job"

    monkeypatch.setattr(beer_garden.db.mongo.models, "Request", request_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "System", system_mock)
    monkeypatch.setattr(beer_garden.db.mongo.models, "Job", job_mock)

    return {
        "request": request_mock,
        "system": system_mock,
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


class TestMigrationScript(object):

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_29_request_migration(self, request_dict):

        del request_dict["id"]
        del request_dict["command_display_name"]

        db = get_db()
        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        ensure_v3_29_model_migration()

        request = request_collection.find_one()
        assert request["command_display_name"] == request["command"]
        request_collection.delete_one({})

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_garden_migration(self, garden_dict):

        del garden_dict["id"]
        garden_dict["status"] = []
        garden_dict["status_info"] = None
        garden_dict["namespaces"] = []

        db = get_db()
        garden_collection = db["garden"]
        garden_collection.insert_one(garden_dict)

        ensure_v3_30_model_migration()

        removed_fields = ["status", "status_info", "namespaces"]
        assert contains_fields("garden", removed_fields) is False
        garden_collection.delete_one({})

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration(self, request_dict, ts_dt):

        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 0}}}}

        del request_dict["id"]
        del request_dict["root_command_type"]

        request_dict["status"] = "SUCCESS"
        request_dict["has_parent"] = False
        request_dict["parent"] = None
        request_dict["created_at"] = ts_dt

        db = get_db()
        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        ensure_v3_30_model_migration()

        request = request_collection.find_one()

        assert request["root_command_type"] == request["command_type"]

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_no_command_type(self, request_dict, ts_dt):

        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 0}}}}

        del request_dict["id"]
        del request_dict["root_command_type"]

        request_dict["status"] = "SUCCESS"
        request_dict["has_parent"] = False
        request_dict["parent"] = None
        request_dict["created_at"] = ts_dt

        db = get_db()
        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        ensure_v3_30_model_migration()

        request = request_collection.find_one()

        assert request["root_command_type"] == "ACTION"
        assert getattr(request, "command_type", None) is None

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_parent_migration(self, request_dict, ts_dt):

        config._CONFIG = {"db": {"prune": {"batch_size": -1, "ttl": {"action": 0}}}}

        del request_dict["id"]
        del request_dict["root_command_type"]

        parent_dict = copy.deepcopy(request_dict)

        parent_dict["status"] = "SUCCESS"
        parent_dict["has_parent"] = False
        parent_dict["parent"] = None
        parent_dict["created_at"] = datetime(2016, 1, 1)

        db = get_db()
        request_collection = db["request"]
        request_collection.insert_one(parent_dict)

        parent = request_collection.find_one({"has_parent": False})

        request_dict["parent"] = DBRef("request", parent["_id"])
        request_dict["status"] = "SUCCESS"
        request_dict["has_parent"] = True
        request_dict["created_at"] = datetime(2017, 1, 1)
        request_dict["command_type"] = "INFO"

        request_collection.insert_one(request_dict)

        ensure_v3_30_model_migration()

        db_parent = request_collection.find_one({"has_parent": False})

        assert db_parent["root_command_type"] == "ACTION"

        db_child = request_collection.find_one({"has_parent": True})

        assert db_child["root_command_type"] == "ACTION"

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_raw_file(self, request_dict, ts_dt):

        db = get_db()
        request_collection = db["request"]
        raw_file_collection = db["raw_file"]
        fs_files_collection = db["fs.files"]
        fs_chunks_collection = db["fs.chunks"]

        del request_dict["id"]
        request_dict["status"] = "SUCCESS"
        request_dict["updated_at"] = datetime(2017, 1, 1)
        request_dict["command_type"] = "INFO"

        request_collection.insert_one(request_dict)

        db_request = request_collection.find_one()

        fs = gridfs.GridFS(db)

        raw_file_data_id = fs.put(b"raw file data")

        raw_file_dict = {"file": raw_file_data_id, "request": db_request["_id"]}

        raw_file_collection.insert_one(raw_file_dict)

        for collection in [
            raw_file_collection,
            fs_files_collection,
            fs_chunks_collection,
        ]:

            pre_migration = collection.find_one()

            assert pre_migration.get("root_command_type") is None
            assert pre_migration.get("status") is None
            assert pre_migration.get("updated_at") is None

        ensure_v3_30_model_migration()

        for collection in [
            raw_file_collection,
            fs_files_collection,
            fs_chunks_collection,
        ]:

            post_migration = collection.find_one()

            assert post_migration.get("root_command_type") == db_request.get(
                "root_command_type"
            )
            assert post_migration.get("status") == db_request.get("status")
            assert post_migration.get("updated_at") is not None

        db.drop_collection("fs.files")
        db.drop_collection("fs.chunks")

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_gridfs(self, request_dict, ts_dt):

        db = get_db()
        request_collection = db["request"]
        fs_files_collection = db["fs.files"]
        fs_chunks_collection = db["fs.chunks"]

        fs = gridfs.GridFS(db)

        output_gridfs_id = fs.put(b"raw file data")
        parameter_gridfs_id = fs.put(b"raw file data")
        del request_dict["id"]
        request_dict["status"] = "SUCCESS"
        request_dict["updated_at"] = datetime(2017, 1, 1)
        request_dict["command_type"] = "INFO"
        request_dict["output_gridfs"] = {"grid_id": output_gridfs_id}
        request_dict["parameters_gridfs"] = {"grid_id": parameter_gridfs_id}

        request_collection.insert_one(request_dict)

        db_request = request_collection.find_one()

        for collection in [
            fs_files_collection,
            fs_chunks_collection,
        ]:

            for pre_migration in collection.find({}):

                assert pre_migration.get("root_command_type") is None
                assert pre_migration.get("status") is None
                assert pre_migration.get("updated_at") is None

        ensure_v3_30_model_migration()

        for collection in [
            fs_files_collection,
            fs_chunks_collection,
        ]:

            for post_migration in collection.find({}):

                assert post_migration.get("root_command_type") == db_request.get(
                    "root_command_type"
                )
                assert post_migration.get("status") == db_request.get("status")
                assert post_migration.get("updated_at") is not None

        db.drop_collection("fs.files")
        db.drop_collection("fs.chunks")

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_file(self, request_dict, ts_dt):

        db = get_db()
        request_collection = db["request"]
        file_collection = db["file"]
        file_chunk_collection = db["file_chunk"]

        del request_dict["id"]
        request_dict["status"] = "SUCCESS"
        request_dict["updated_at"] = datetime(2017, 1, 1)
        request_dict["command_type"] = "INFO"

        request_collection.insert_one(request_dict)

        db_request = request_collection.find_one()

        file_collection.insert_one(
            {"owner_type": "REQUEST", "request": db_request["_id"]}
        )
        db_file = file_collection.find_one()
        file_chunk_collection.insert_one({"file_id": str(db_file["_id"])})

        for collection in [file_collection, file_chunk_collection]:

            pre_migration = collection.find_one()

            assert pre_migration.get("root_command_type") is None
            assert pre_migration.get("status") is None
            assert pre_migration.get("updated_at") is None

        ensure_v3_30_model_migration()

        for collection in [file_collection, file_chunk_collection]:

            post_migration = collection.find_one()

            assert post_migration.get("root_command_type") == db_request.get(
                "root_command_type"
            )
            assert post_migration.get("status") == db_request.get("status")
            assert post_migration.get("updated_at") is not None


class TestCheckIndexes(object):
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_same_indexes(self, model_mocks):
        for model_mock in model_mocks.values():
            model_mock._meta = {"indexes": [{"name": "index1_index"}]}
            model_mock._get_collection = Mock(
                return_value=Mock(
                    index_information=Mock(return_value={"index1_index": {}})
                )
            )
            model_mock.create_index = Mock()

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        for model_mock in model_mocks.values():
            assert model_mock.create_index.call_count == 0

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_missing_index(self, model_mocks):
        for model_mock in model_mocks.values():
            model_mock._meta = {
                "indexes": [{"name": "index1_index"}, {"name": "index2_index"}]
            }

            mock_collection = Mock()
            mock_collection.index_information = Mock(return_value={"index1_index": {}})
            mock_collection.drop_index = Mock()

            model_mock._get_collection = Mock(return_value=mock_collection)

            model_mock.create_index = Mock()

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        for model_mock in model_mocks.values():
            assert model_mock.create_index.call_count == 1

    @patch("mongoengine.connection.get_db")
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_successful_index_rebuild(self, get_db_mock, model_mocks):
        # 'normal' return values
        for model_mock in model_mocks.values():
            model_mock._meta = {"indexes": [{"name": "index1_index"}]}
            mock_collection = Mock()
            mock_collection.index_information = Mock(return_value={"index1_index": {}})
            mock_collection.drop_index = Mock()

            model_mock._get_collection = Mock(return_value=mock_collection)

        # ... except for this one
        model_mocks["request"]._meta["indexes"] = []

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [beer_garden.db.mongo.util.check_indexes(doc) for doc in model_mocks.values()]
        assert model_mocks["request"]._get_collection().drop_index.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db")
    def test_unsuccessful_index_drop(self, get_db_mock, model_mocks):
        for model_mock in model_mocks.values():
            model_mock._meta = {"indexes": [{"name": "index1_index"}]}

            mock_collection = Mock()
            mock_collection.index_information = Mock(return_value={"index2_index": {}})
            mock_collection.drop_index = Mock(side_effect=IndexOperationError(""))
            mock_collection.drop_indexes = Mock(side_effect=IndexOperationError(""))

            model_mock._get_collection = Mock(return_value=mock_collection)

        get_db_mock.side_effect = IndexOperationError("")

        for doc in model_mocks.values():
            with pytest.raises(IndexOperationError):
                beer_garden.db.mongo.util.check_indexes(doc)

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db", MagicMock())
    def test_unsuccessful_index_rebuild(self, model_mocks):
        for model_mock in model_mocks.values():
            model_mock._meta = {"indexes": [{"name": "index2_index"}]}
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"_id_": {}})
                )
            )

            model_mock.create_index = Mock(side_effect=IndexOperationError(""))
            model_mock.ensure_indexes.side_effect = IndexOperationError("")

        for doc in model_mocks.values():
            with pytest.raises(IndexOperationError):
                beer_garden.db.mongo.util.check_indexes(doc)

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.connection.get_db", MagicMock())
    def test_unsuccessful_read_objects(self, model_mocks):
        for model_mock in model_mocks.values():
            model_mock._meta = {"indexes": [{"name": "index1_index"}]}
            model_mock._get_collection = Mock(
                return_value=MagicMock(
                    index_information=Mock(return_value={"index1_index": {}})
                )
            )

            model_mock.objects.first.side_effect = FieldDoesNotExist("")

        for doc in model_mocks.values():
            with pytest.raises(FieldDoesNotExist):
                beer_garden.db.mongo.util.check_indexes(doc)

    @patch("mongoengine.connection.get_db")
    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_old_request_index(self, get_db_mock, model_mocks, monkeypatch):
        # 'normal' return values
        for model_mock in model_mocks.values():

            model_mock._meta = {"indexes": [{"name": "index1_index"}]}
            mock_collection = Mock()
            mock_collection.index_information = Mock(return_value={"index1_index": {}})
            mock_collection.drop_index = Mock()

            model_mock._get_collection = Mock(return_value=mock_collection)

        # ... except for this one
        model_mocks[
            "request"
        ]._get_collection.return_value.index_information.return_value = {
            "index1_index": {},
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
        assert model_mocks["request"]._get_collection().drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True
        assert update_parent_field_type_mock.called is True
        assert update_has_parent_mock.called is True


class TestEnsureLocalGarden:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def teardown_method(self):
        beer_garden.db.mongo.models.Garden.drop_collection()

    def test_ensure_local_garden_creates_new_garden_from_config(self, monkeypatch):
        """ensure_local_garden should create a Garden entry in the database with
        name derived from the "garden.name" config setting and a connection type of
        LOCAL"""

        config._CONFIG = {"garden": {"name": "parent"}, "parent": {"sync_interval": 1}}

        ensure_local_garden()
        garden = Garden.objects.get(connection_type="LOCAL")

        assert garden.name == config.get("garden.name")

    def test_ensure_local_garden_updates_garden_from_config(self, monkeypatch):
        """ensure_local_garden should update the name of an existing Garden entry in the
        database with a connection type of LOCAL"""
        config._CONFIG = {"garden": {"name": "parent"}, "parent": {"sync_interval": 1}}

        Garden(name="thisshouldchange", connection_type="LOCAL").save()
        ensure_local_garden()
        garden = Garden.objects.get(connection_type="LOCAL")

        assert garden.name == config.get("garden.name")
