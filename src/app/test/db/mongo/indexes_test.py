# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock, Mock, patch
from mongoengine.errors import FieldDoesNotExist

import beer_garden.db.mongo.indexes
from beer_garden.errors import IndexOperationError


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


# @pytest.fixture
# def config_mock_value(monkeypatch):
#     def config_get_value(config_name):
#         return "somevalue"

#     monkeypatch.setattr(config, "get", config_get_value)


# @pytest.fixture
# def config_mock_none(monkeypatch):
#     def config_get_value(config_name):
#         return None

#     monkeypatch.setattr(config, "get", config_get_value)


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

        [
            beer_garden.db.mongo.indexes.check_indexes(doc)
            for doc in model_mocks.values()
        ]
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

        [
            beer_garden.db.mongo.indexes.check_indexes(doc)
            for doc in model_mocks.values()
        ]
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

        [
            beer_garden.db.mongo.indexes.check_indexes(doc)
            for doc in model_mocks.values()
        ]
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
                beer_garden.db.mongo.indexes.check_indexes(doc)

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
                beer_garden.db.mongo.indexes.check_indexes(doc)

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
                beer_garden.db.mongo.indexes.check_indexes(doc)

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
        update_has_parent_mock = Mock()
        monkeypatch.setattr(
            beer_garden.db.mongo.indexes,
            "_update_request_has_parent_model",
            update_has_parent_mock,
        )

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        [
            beer_garden.db.mongo.indexes.check_indexes(doc)
            for doc in model_mocks.values()
        ]
        assert model_mocks["request"]._get_collection().drop_indexes.call_count == 1
        assert model_mocks["request"].ensure_indexes.called is True
        assert update_has_parent_mock.called is True
