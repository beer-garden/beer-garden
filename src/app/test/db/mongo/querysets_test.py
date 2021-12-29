# -*- coding: utf-8 -*-
import pytest
from mock import Mock
from mongoengine import Document, GridFSProxy, fields
from mongomock.gridfs import enable_gridfs_integration

from beer_garden.db.mongo.querysets import FileFieldHandlingQuerySet

FILE_COUNT = 3

enable_gridfs_integration()


class ModelWithFileField(Document):
    file_field = fields.FileField()

    meta = {"queryset_class": FileFieldHandlingQuerySet}


@pytest.fixture()
def model_instances():
    for _ in range(FILE_COUNT):
        ModelWithFileField().save()

    yield
    ModelWithFileField.drop_collection()


class TestFileFieldHandlingQuerySet:
    def test_delete_calls_file_field_delete(self, monkeypatch, model_instances):
        monkeypatch.setattr(GridFSProxy, "delete", Mock())
        ModelWithFileField.objects.all().delete()

        assert GridFSProxy.delete.call_count == FILE_COUNT


class TestFileFieldHandlingQuerySetNoCache:
    def test_delete_calls_file_field_delete(self, monkeypatch, model_instances):
        monkeypatch.setattr(GridFSProxy, "delete", Mock())
        ModelWithFileField.objects.all().no_cache().delete()

        assert GridFSProxy.delete.call_count == FILE_COUNT
