# -*- coding: utf-8 -*-
import copy
from datetime import datetime

import gridfs
import pytest
from bson.dbref import DBRef
from mock import Mock, patch
from mongoengine.connection import get_db

from beer_garden import config
from beer_garden.db.mongo.migration import (  # ensure_roles,; ensure_users,
    contains_fields,
    ensure_v3_29_model_migration,
    ensure_v3_30_model_migration,
    ensure_v3_XX_model_migration,
)


@pytest.fixture(autouse=True)
def drop():
    yield
    db = get_db()
    for collection in db.list_collection_names():
        db[collection].drop()


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
        request_dict["output_gridfs"] = output_gridfs_id
        request_dict["parameters_gridfs"] = parameter_gridfs_id

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

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_no_target_garden(self, request_dict, ts_dt):

        config._CONFIG = {"garden": {"name": "test_garden"}}

        del request_dict["target_garden"]

        db = get_db()
        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        ensure_v3_30_model_migration()

        request = request_collection.find_one()

        assert request["target_garden"] == "test_garden"

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_request_migration_no_source_garden(self, request_dict, ts_dt):

        config._CONFIG = {"garden": {"name": "test_garden"}}

        del request_dict["source_garden"]

        db = get_db()
        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        ensure_v3_30_model_migration()

        request = request_collection.find_one()

        assert request["source_garden"] == "test_garden"

    def test_3_30_system_garden_name_migration(self, system_dict):
        config._CONFIG = {"garden": {"name": "localgarden"}}

        del system_dict["id"]
        system_dict["local"] = True
        del system_dict["garden_name"]
        db = get_db()
        system_collection = db["system"]
        system_collection.insert_one(system_dict)

        non_migrated_system = system_collection.find_one({})

        assert not hasattr(non_migrated_system, "garden_name")

        ensure_v3_30_model_migration()

        migrated_system = system_collection.find_one({})
        assert migrated_system["garden_name"] == "localgarden"

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_30_system_garden_name_migration_downstream(
        self, system_dict, garden_dict
    ):
        config._CONFIG = {"garden": {"name": "localgarden"}}

        del system_dict["id"]
        system_dict["local"] = False
        del system_dict["garden_name"]
        db = get_db()
        system_collection = db["system"]
        system_collection.insert_one(system_dict)

        non_migrated_system = system_collection.find_one({})

        assert not hasattr(non_migrated_system, "garden_name")

        garden_dict["systems"] = [non_migrated_system["_id"]]
        del garden_dict["receiving_connections"]
        del garden_dict["publishing_connections"]
        del garden_dict["id"]
        garden_collection = db["garden"]
        garden_collection.insert_one(garden_dict)

        ensure_v3_30_model_migration()

        migrated_system = system_collection.find_one({})
        assert migrated_system["garden_name"] == garden_dict["name"]

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_XX_migrate_gridfs_output(self, request_dict):
        db = get_db()

        # Create Gridfs File
        fs = gridfs.GridFS(db)
        output_data_id = fs.put(b"raw file data")

        # Create request with output_gridfs
        request_dict["output"] = None
        request_dict["output_gridfs"] = output_data_id

        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        assert (
            request_collection.count_documents({"output_gridfs": {"$exists": True}})
            == 1
        )

        ensure_v3_XX_model_migration()

        assert (
            request_collection.count_documents({"output_gridfs": {"$exists": True}})
            == 0
        )

        loaded_request = request_collection.find_one({})
        assert db["fs.files"].find_one({})["request_id"] == str(loaded_request["_id"])
        assert db["fs.chunks"].find_one({})["request_id"] == str(loaded_request["_id"])

        for field in ["status", "updated_at", "root_command_type"]:
            assert db["fs.files"].find_one({})[field] == loaded_request[field]
            assert db["fs.chunks"].find_one({})[field] == loaded_request[field]

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_XX_migrate_gridfs_parameters(self, request_dict):
        db = get_db()

        # Create Gridfs File
        fs = gridfs.GridFS(db)
        output_data_id = fs.put(b"raw file data")

        # Create request with output_gridfs
        request_dict["parameters"] = None
        request_dict["parameters_gridfs"] = output_data_id

        request_collection = db["request"]
        request_collection.insert_one(request_dict)

        assert (
            request_collection.count_documents({"parameters_gridfs": {"$exists": True}})
            == 1
        )

        ensure_v3_XX_model_migration()

        assert (
            request_collection.count_documents({"parameters_gridfs": {"$exists": True}})
            == 0
        )

        loaded_request = request_collection.find_one({})
        assert db["fs.files"].find_one({})["request_id"] == str(loaded_request["_id"])
        assert db["fs.chunks"].find_one({})["request_id"] == str(loaded_request["_id"])

        for field in ["status", "updated_at", "root_command_type"]:
            assert db["fs.files"].find_one({})[field] == loaded_request[field]
            assert db["fs.chunks"].find_one({})[field] == loaded_request[field]

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_XX_migrate_file_job(self, job_dict):
        db = get_db()

        job_collection = db["job"]
        job_collection.insert_one(job_dict)
        loaded_job = job_collection.find_one({})

        file_collection = db["file"]
        file_collection.insert_one(
            {"file_name": "test", "job": DBRef("job", loaded_job["_id"])}
        )
        loaded_file = file_collection.find_one({})

        file_chunk_collection = db["file_chunk"]
        file_chunk_collection.insert_one(
            {"file_id": loaded_file["_id"], "data": "my data"}
        )

        assert file_collection.count_documents({"job": {"$exists": True}}) == 1

        assert (
            file_chunk_collection.count_documents({"owner_type": {"$exists": True}})
            == 0
        )

        ensure_v3_XX_model_migration()

        assert file_collection.count_documents({"job": {"$exists": True}}) == 0
        assert (
            file_chunk_collection.count_documents({"owner_type": {"$exists": True}})
            == 1
        )

        assert file_collection.find_one({})["owner_id"] == str(loaded_job["_id"])
        assert file_chunk_collection.find_one({})["owner_type"] == "JOB"

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_XX_migrate_file_request(self, request_dict):
        db = get_db()

        request_collection = db["request"]
        request_collection.insert_one(request_dict)
        loaded_request = request_collection.find_one({})

        file_collection = db["file"]
        file_collection.insert_one(
            {"file_name": "test", "request": DBRef("request", loaded_request["_id"])}
        )
        loaded_file = file_collection.find_one({})

        file_chunk_collection = db["file_chunk"]
        file_chunk_collection.insert_one(
            {"file_id": loaded_file["_id"], "data": "my data"}
        )

        assert file_collection.count_documents({"request": {"$exists": True}}) == 1

        assert (
            file_chunk_collection.count_documents({"owner_type": {"$exists": True}})
            == 0
        )

        ensure_v3_XX_model_migration()

        assert file_collection.count_documents({"request": {"$exists": True}}) == 0
        assert (
            file_chunk_collection.count_documents({"owner_type": {"$exists": True}})
            == 1
        )

        assert file_collection.find_one({})["owner_id"] == str(loaded_request["_id"])
        assert file_chunk_collection.find_one({})["owner_type"] == "REQUEST"

    @patch("mongoengine.connect", Mock())
    @patch("mongoengine.register_connection", Mock())
    def test_3_XX_migrate_raw_file(self, request_dict):
        db = get_db()

        request_collection = db["request"]
        raw_file_collection = db["raw_file"]

        request_collection.insert_one(request_dict)

        db_request = request_collection.find_one()

        fs = gridfs.GridFS(db)

        raw_file_data_id = fs.put(b"raw file data")

        raw_file_dict = {"file": raw_file_data_id, "request": db_request["_id"]}

        raw_file_collection.insert_one(raw_file_dict)

        assert raw_file_collection.count_documents({"request": {"$exists": True}}) == 1

        ensure_v3_XX_model_migration()

        assert raw_file_collection.count_documents({"request": {"$exists": True}}) == 0

        loaded_request = request_collection.find_one({})
        assert db["fs.files"].find_one({})["request_id"] == str(loaded_request["_id"])
        assert db["fs.chunks"].find_one({})["request_id"] == str(loaded_request["_id"])

        for field in ["status", "updated_at", "root_command_type"]:
            assert db["fs.files"].find_one({})[field] == loaded_request[field]
            assert db["fs.chunks"].find_one({})[field] == loaded_request[field]
